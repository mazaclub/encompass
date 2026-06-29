"""Export wallet transaction history for external apps and databases."""

import csv
import datetime
import json
import sys

from util import format_satoshis


def build_history_records(wallet):
    """Return wallet history rows as plain dicts suitable for JSON/CSV export."""
    records = []
    for item in wallet.get_tx_history():
        tx_hash, confirmations, _is_mine, value, fee, balance, timestamp = item
        if confirmations and timestamp is not None:
            try:
                time_string = datetime.datetime.fromtimestamp(timestamp).isoformat(" ")[:-3]
            except (RuntimeError, TypeError, NameError):
                time_string = "unknown"
        else:
            time_string = "pending"

        if value is not None:
            value_string = format_satoshis(value, True)
        else:
            value_string = "--"

        if fee is not None:
            fee_string = format_satoshis(fee, True)
        else:
            fee_string = "0"

        if tx_hash:
            label, _is_default_label = wallet.get_label(tx_hash)
            if not isinstance(label, str):
                label = label.decode("utf-8") if hasattr(label, "decode") else str(label)
        else:
            label = ""

        records.append(
            {
                "txid": tx_hash,
                "label": label,
                "confirmations": confirmations,
                "value": value_string,
                "fee": fee_string,
                "balance": format_satoshis(balance, False),
                "timestamp": time_string,
            }
        )
    return records


def export_txids_only(records):
    """Return unique transaction ids in wallet history order."""
    seen = set()
    txids = []
    for row in records:
        txid = row.get("txid")
        if txid and txid not in seen:
            seen.add(txid)
            txids.append(txid)
    return txids


def write_history_export(wallet, file_name, export_format="json"):
    """Write wallet history to a file or stdout when file_name is '-'."""
    records = build_history_records(wallet)
    export_format = (export_format or "json").lower()

    if export_format == "txids":
        payload = export_txids_only(records)
        if file_name == "-":
            for txid in payload:
                sys.stdout.write(txid + "\n")
            return len(payload)
        with open(file_name, "w") as handle:
            json.dump(payload, handle, indent=2)
        return len(payload)

    if export_format == "csv":
        fieldnames = [
            "txid",
            "label",
            "confirmations",
            "value",
            "fee",
            "balance",
            "timestamp",
        ]
        if file_name == "-":
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()
            for row in records:
                writer.writerow(row)
        else:
            with open(file_name, "w") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for row in records:
                    writer.writerow(row)
        return len(records)

    if file_name == "-":
        sys.stdout.write(json.dumps(records, indent=2))
    else:
        with open(file_name, "w") as handle:
            json.dump(records, handle, indent=4)
    return len(records)

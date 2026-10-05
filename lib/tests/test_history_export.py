import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from history_export import build_history_records, export_txids_only, write_history_export


class FakeWallet(object):
    def get_tx_history(self):
        return [
            ("abc111", 3, True, 100000, 1000, 200000, 1700000000),
            ("def222", 0, True, -50000, 500, 150000, None),
        ]

    def get_label(self, tx_hash):
        return ("payment-%s" % tx_hash[:3], False)


class HistoryExportTestCase(unittest.TestCase):
    def test_build_history_records(self):
        records = build_history_records(FakeWallet())
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["txid"], "abc111")
        self.assertEqual(records[0]["label"], "payment-abc")
        self.assertEqual(records[1]["timestamp"], "pending")

    def test_export_txids_only(self):
        records = build_history_records(FakeWallet())
        self.assertEqual(export_txids_only(records), ["abc111", "def222"])

    def test_write_json_file(self):
        path = os.path.join(tempfile.mkdtemp(), "history.json")
        count = write_history_export(FakeWallet(), path, "json")
        self.assertEqual(count, 2)
        data = json.load(open(path))
        self.assertEqual(data[0]["txid"], "abc111")

    def test_write_txids_file(self):
        path = os.path.join(tempfile.mkdtemp(), "txids.json")
        count = write_history_export(FakeWallet(), path, "txids")
        self.assertEqual(count, 2)
        data = json.load(open(path))
        self.assertEqual(data, ["abc111", "def222"])

    def test_write_csv_file(self):
        path = os.path.join(tempfile.mkdtemp(), "history.csv")
        count = write_history_export(FakeWallet(), path, "csv")
        self.assertEqual(count, 2)
        text = open(path).read()
        self.assertIn("txid", text)
        self.assertIn("abc111", text)


if __name__ == "__main__":
    unittest.main()

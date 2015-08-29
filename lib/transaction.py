#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2011 thomasv@gitorious
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


# Note: The deserialization code originally comes from ABE.


import bitcoin
from bitcoin import *
from base58 import public_key_to_bc_address, hash_160_to_bc_address, bc_address_to_hash_160, hash_160
from util import print_error
from util_coin import var_int, int_to_hex, op_push, hash_encode
from script import *
import time
import chainparams
from chainparams import run_chainhook
import hashes

def parse_redeemScript(bytes):
    dec = [ x for x in script_GetOp(bytes.decode('hex')) ]

    # 2 of 2
    match = [ opcodes.OP_2, opcodes.OP_PUSHDATA4, opcodes.OP_PUSHDATA4, opcodes.OP_2, opcodes.OP_CHECKMULTISIG ]
    if match_decoded(dec, match):
        pubkeys = [ dec[1][1].encode('hex'), dec[2][1].encode('hex') ]
        return 2, pubkeys

    # 2 of 3
    match = [ opcodes.OP_2, opcodes.OP_PUSHDATA4, opcodes.OP_PUSHDATA4, opcodes.OP_PUSHDATA4, opcodes.OP_3, opcodes.OP_CHECKMULTISIG ]
    if match_decoded(dec, match):
        pubkeys = [ dec[1][1].encode('hex'), dec[2][1].encode('hex'), dec[3][1].encode('hex') ]
        return 2, pubkeys



def parse_sig(x_sig):
    s = []
    for sig in x_sig:
        if sig[-2:] == '01':
            s.append(sig[:-2])
        else:
            assert sig == NO_SIGNATURE
            s.append(None)
    return s

def is_extended_pubkey(x_pubkey):
    return x_pubkey[0:2] in ['fe', 'ff']

def x_to_xpub(x_pubkey):
    if x_pubkey[0:2] == 'ff':
        from account import BIP32_Account
        xpub, s = BIP32_Account.parse_xpubkey(x_pubkey)
        return xpub



def parse_xpub(x_pubkey, active_chain=None):
    if active_chain is None:
        active_chain = chainparams.get_active_chain()
    if x_pubkey[0:2] in ['02','03','04']:
        pubkey = x_pubkey
    elif x_pubkey[0:2] == 'ff':
        from account import BIP32_Account
        xpub, s = BIP32_Account.parse_xpubkey(x_pubkey)
        pubkey = BIP32_Account.derive_pubkey_from_xpub(xpub, s[0], s[1])
    elif x_pubkey[0:2] == 'fe':
        from account import OldAccount
        mpk, s = OldAccount.parse_xpubkey(x_pubkey)
        pubkey = OldAccount.get_pubkey_from_mpk(mpk.decode('hex'), s[0], s[1])
    elif x_pubkey[0:2] == 'fd':
        addrtype = ord(x_pubkey[2:4].decode('hex'))
        hash160 = x_pubkey[4:].decode('hex')
        pubkey = None
        address = hash_160_to_bc_address(hash160, active_chain.p2pkh_version)
    else:
        raise BaseException("Cannnot parse pubkey")
    if pubkey:
        address = public_key_to_bc_address(pubkey.decode('hex'), active_chain.p2pkh_version)
    return pubkey, address


def parse_scriptSig(d, bytes, active_chain=None):
    if active_chain is None:
        active_chain = chainparams.get_active_chain()
    try:
        decoded = [ x for x in script_GetOp(bytes) ]
    except Exception:
        # coinbase transactions raise an exception
        print_error("cannot find address in input script", bytes.encode('hex'))
        return

    # payto_pubkey
    match = [ opcodes.OP_PUSHDATA4 ]
    if match_decoded(decoded, match):
        sig = decoded[0][1].encode('hex')
        d['address'] = "(pubkey)"
        d['signatures'] = [sig]
        d['num_sig'] = 1
        d['x_pubkeys'] = ["(pubkey)"]
        d['pubkeys'] = ["(pubkey)"]
        return

    # non-generated TxIn transactions push a signature
    # (seventy-something bytes) and then their public key
    # (65 bytes) onto the stack:
    match = [ opcodes.OP_PUSHDATA4, opcodes.OP_PUSHDATA4 ]
    if match_decoded(decoded, match):
        sig = decoded[0][1].encode('hex')
        x_pubkey = decoded[1][1].encode('hex')
        try:
            signatures = parse_sig([sig])
            pubkey, address = parse_xpub(x_pubkey, active_chain)
        except:
            import traceback
            traceback.print_exc(file=sys.stdout)
            print_error("cannot find address in input script", bytes.encode('hex'))
            return
        d['signatures'] = signatures
        d['x_pubkeys'] = [x_pubkey]
        d['num_sig'] = 1
        d['pubkeys'] = [pubkey]
        d['address'] = address
        return

    # p2sh transaction, m of n
    match = [ opcodes.OP_0 ]
    while len(match) < len(decoded):
        match.append(opcodes.OP_PUSHDATA4)

    if not match_decoded(decoded, match):
        print_error("cannot find address in input script", bytes.encode('hex'))
        return

    x_sig = map(lambda x:x[1].encode('hex'), decoded[1:-1])
    d['signatures'] = parse_sig(x_sig)

    dec2 = [ x for x in script_GetOp(decoded[-1][1]) ]
    multis_m = multis_n = None
    multis_mn = match_decoded_multisig(dec2)
    if multis_mn:
        multis_m = multis_mn[0]
        multis_n = multis_mn[1]
        x_pubkeys = map(lambda x:x[1].encode('hex'), dec2[1:-2])
        d['num_sig'] = multis_m
    else:
        print_error("cannot find address in input script", bytes.encode('hex'))
        return

    d['x_pubkeys'] = x_pubkeys
    pubkeys = map(lambda x: parse_xpub(x)[0], x_pubkeys)
    d['pubkeys'] = pubkeys
    redeemScript = multisig_script(pubkeys,multis_m)
    d['redeemScript'] = redeemScript
    d['address'] = hash_160_to_bc_address(hash_160(redeemScript.decode('hex')), active_chain.p2sh_version)


def _get_address_from_output_script(decoded, matches, active_chain=None):
    """Find address in output script. matches is a list of tuples of the form:
        ( opcodes_to_match (list),
        address type (str),
        index in script where address is (int),
        actions to take on extracted data (list) )

        actions to take on extracted data may contain one or more of
        the following to have the corresponding effect on the extracted data, "data":
            - 'encode': data.encode('hex')
            - 'address': hash_160_to_bc_address(data, p2pkh_version)
            - 'p2sh': hash_160_to_bc_address(data, p2sh_version)

    """
    if active_chain is None: active_chain = chainparams.get_active_chain()
    for match, addr_type, data_index, actions in matches:
        if match_decoded(decoded, match):
            data = decoded[data_index][1]

            # Convert to address
            if addr_type == 'address':
                addr_version = active_chain.p2pkh_version
                if 'p2sh' in actions:
                    addr_version = active_chain.p2sh_version
                data = hash_160_to_bc_address(data, addr_version)
            # Encode in hex if necessary
            if 'encode' in actions:
                data = data.encode('hex')

            return addr_type, data

    return "(None)", "(None)"

def get_address_from_output_script(bytes, active_chain=None):
    if active_chain is None:
        active_chain = chainparams.get_active_chain()
    decoded = [ x for x in script_GetOp(bytes) ]

    # list of (opcodes_list, addr_type, addr_data_index, [actions_to_take])
    # actions_to_take contains things such as 'encode' if the data should be hex-encoded.
    matches = [
        # The Genesis Block, self-payments, and pay-by-IP-address payments
        ([ opcodes.OP_PUSHDATA4, opcodes.OP_CHECKSIG ], 'pubkey', 0, ['encode']),
        # Pay-to-Public-Key-Hash
        ([ opcodes.OP_DUP, opcodes.OP_HASH160, opcodes.OP_PUSHDATA4, opcodes.OP_EQUALVERIFY, opcodes.OP_CHECKSIG ], 'address', 2, [None]),
        # Pay-to-Script-Hash
        ([ opcodes.OP_HASH160, opcodes.OP_PUSHDATA4, opcodes.OP_EQUAL ], 'address', 1, ['p2sh']),
        # OP_RETURN (null output)
        ([ opcodes.OP_RETURN, opcodes.OP_PUSHDATA4 ], 'op_return', 1, [None])
    ]

    run_chainhook('transaction_get_address_from_output_script', opcodes, matches)

    return _get_address_from_output_script(decoded, matches, active_chain)






def parse_input(vds, active_chain=None):
    d = {}
    prevout_hash = hash_encode(vds.read_bytes(32))
    prevout_n = vds.read_uint32()
    scriptSig = vds.read_bytes(vds.read_compact_size())
    d['scriptSig'] = scriptSig.encode('hex')
    sequence = vds.read_uint32()
    if prevout_hash == '00'*32:
        d['is_coinbase'] = True
    else:
        d['is_coinbase'] = False
        d['prevout_hash'] = prevout_hash
        d['prevout_n'] = prevout_n
        d['sequence'] = sequence
        d['pubkeys'] = []
        d['signatures'] = {}
        d['address'] = None
        if scriptSig:
            parse_scriptSig(d, scriptSig, active_chain)
    return d


def parse_output(vds, i, active_chain=None):
    d = {}
    d['value'] = vds.read_int64()
    scriptPubKey = vds.read_bytes(vds.read_compact_size())
    d['type'], d['address'] = get_address_from_output_script(scriptPubKey, active_chain)
    d['scriptPubKey'] = scriptPubKey.encode('hex')
    d['prevout_n'] = i
    return d

def deserialize_tx_fields(vds, d, fields, active_chain=None):
    """Deserialize a data stream according to the given fields.

    Fields is a list of 3-tuples: (name, action, add_to_dict)
        name is the Transaction attribute to assign the extracted value to.
        action is either a method of BCDataStream, or one of the following:
            'parse_inputs': Extract inputs from stream
            'parse_outputs': Extract output from stream
            'read_bytes_compact_size': Calls vds.read_bytes(vds.read_compact_size())
        add_to_dict specifies whether to set a Transaction attribute to the extracted
        data, or only use it within this function.

    """
    # dd is a separate dict containing data that doesn't go
    # in the tx dict.
    dd = {}
    for name, action, add_to_dict in fields:
        # special cases
        if action == 'parse_inputs':
            d[name] = list(parse_input(vds, active_chain) for i in xrange(dd['vin']))
        elif action == 'parse_outputs':
            d[name] = list(parse_output(vds,i, active_chain) for i in xrange(dd['vout']))
        elif action == 'read_bytes_compact_size':
            try:
                if add_to_dict:
                    d[name] = vds.read_bytes(vds.read_compact_size())
                else:
                    dd[name] = vds.read_bytes(vds.read_compact_size())
            except Exception:
                continue
        else:
            if add_to_dict:
                d[name] = action()
            else:
                dd[name] = action()

def deserialize(raw, active_chain=None):
    vds = BCDataStream()
    vds.write(raw.decode('hex'))

    fields = [('version', vds.read_int32, True),        # version
            ('vin', vds.read_compact_size, False),      # vin
            ('inputs', 'parse_inputs', True),           # inputs
            ('vout', vds.read_compact_size, False),     # vout
            ('outputs', 'parse_outputs', True),         # outputs
            ('lockTime', vds.read_uint32, True) ]       # locktime

    run_chainhook('transaction_deserialize_tx_fields', vds, fields)

    d = {}
    start = vds.read_cursor
    deserialize_tx_fields(vds, d, fields, active_chain)
    return d

class Transaction:

    def __str__(self):
        if self.raw is None:
            self.raw = self.serialize()
        return self.raw

    def __init__(self, inputs, outputs, locktime=0, active_chain=None):
        """Create a new transaction.

        Args:
            inputs (list): List of dicts. An input is a dict with the following items:

                - coinbase (bool): Whether this is a coinbase input.
                - prevout_hash (str): TxID containing the output that this input spends.
                - prevout_n (int): Index of the output that this input spends.
                - value (int): Value of the output that this input spends, in satoshis.
                - address (str): Address of key(s) in this input's scriptSig.
                - num_sig (int): Number of signatures this input requires.
                - pubkeys (list): Strings of public keys in hex.
                - x_pubkeys (list): Strings of extended public keys in hex.
                - signatures (list): Strings of signatures in hex.

                P2PKH inputs have a 'redeemPubkey' key; P2SH inputs have a 'redeemScript' key.

            outputs (list): List of tuples. Output format:
                (type, address, value)

                - type is 'address' for P2PKH outputs, 'pubkey' for P2PK outputs,
                or 'op_return' for null data outputs.
                - address is an address for P2PKH outputs, a pubkey for P2PK outputs,
                or raw bytes for null data outputs.

        """
        self.inputs = inputs
        self.outputs = outputs
        self.locktime = locktime
        self.raw = None
        if active_chain is None:
            active_chain = chainparams.get_active_chain()
        self.active_chain = active_chain

    @classmethod
    def deserialize(klass, raw, active_chain=None):
        self = klass([],[], active_chain=active_chain)
        self.update(raw)
        return self

    def update(self, raw):
        d = deserialize(raw, self.active_chain)
        self.raw = raw
        self.inputs = d['inputs']
        self.outputs = map(lambda x: (x['type'], x['address'], x['value']), d['outputs'])
        self.locktime = d['lockTime']
        for k, v in d.items():
            if not k in ['inputs', 'outputs', 'lockTime']:
                setattr(self, k, v)

    @classmethod
    def sweep(klass, privkeys, network, to_address, fee, active_chain=None):
        if active_chain is None:
            active_chain = chainparams.get_active_chain()
        self.active_chain = active_chain
        inputs = []
        for privkey in privkeys:
            pubkey = public_key_from_private_key(privkey, self.active_chain.wif_version)
            address = address_from_private_key(privkey,
                self.active_chain.p2pkh_version, self.active_chain.wif_version)
            u = network.synchronous_get([ ('blockchain.address.listunspent',[address])])[0]
            pay_script = klass.pay_script('address', address)
            for item in u:
                item['scriptPubKey'] = pay_script
                item['redeemPubkey'] = pubkey
                item['address'] = address
                item['prevout_hash'] = item['tx_hash']
                item['prevout_n'] = item['tx_pos']
                item['pubkeys'] = [pubkey]
                item['x_pubkeys'] = [None]
                item['signatures'] = [None]
                item['num_sig'] = 1
            inputs += u

        if not inputs:
            return

        total = sum( map(lambda x:int(x.get('value')), inputs) ) - fee
        outputs = [('address', to_address, total)]
        self = klass(inputs, outputs)
        self.sign({ pubkey:privkey })
        return self

    @classmethod
    def multisig_script(klass, public_keys, num=None):
        """Deprecated. Use script.multisig_script."""
        return multisig_script(public_keys, num)


    @classmethod
    def pay_script(self, type, addr, active_chain=None):
        if active_chain is None:
            active_chain = chainparams.get_active_chain()
        self.active_chain = active_chain
        if type == 'op_return':
            return null_output_script(addr)
        else:
            assert type == 'address'
        script = []
        addrtype, hash_160 = bc_address_to_hash_160(addr)
        if addrtype == self.active_chain.p2pkh_version:
            script.append(p2pkh_script(hash_160))
        elif addrtype == self.active_chain.p2sh_version:
            script.append(p2sh_script(hash_160))
        else:
            raise
        return ''.join(script)

    def serialize_input(self, i, for_sig=None):
        txin = self.inputs[i]

        s = []

        s.append( txin['prevout_hash'].decode('hex')[::-1].encode('hex') )   # prev hash
        s.append( int_to_hex(txin['prevout_n'],4) )                          # prev index

        p2sh = txin.get('redeemScript') is not None
        num_sig = txin['num_sig']
        address = txin['address']

        x_signatures = txin['signatures']
        signatures = filter(lambda x: x is not None, x_signatures)
        is_complete = len(signatures) == num_sig

        if for_sig in [-1, None]:
            # if we have enough signatures, we use the actual pubkeys
            # use extended pubkeys (with bip32 derivation)
            sig_list = []
            if for_sig == -1:
                # we assume that signature will be 0x48 bytes long
                pubkeys = txin['pubkeys']
                sig_list = [ "00"* 0x48 ] * num_sig
            elif is_complete:
                pubkeys = txin['pubkeys']
                for signature in signatures:
                    sig_list.append(signature + '01')
            else:
                pubkeys = txin['x_pubkeys']
                for signature in x_signatures:
                    sig_list.append((signature + '01') if signature is not None else NO_SIGNATURE)

            sig_list = ''.join( map( lambda x: push_script(x), sig_list))
            if not p2sh:
                script = sig_list
                x_pubkey = pubkeys[0]
                if x_pubkey is None:
                    addrtype, h160 = bc_address_to_hash_160(txin['address'])
                    x_pubkey = 'fd' + (chr(addrtype) + h160).encode('hex')
                script += push_script(x_pubkey)
            else:
                script = '00'                                       # op_0
                script += sig_list
                redeem_script = multisig_script(pubkeys,num_sig)
                script += push_script(redeem_script)

        elif for_sig==i:
            script = txin['redeemScript'] if p2sh else self.pay_script('address', address)
        else:
            script = ''

        s.append(var_int( len(script)/2 ))                          # script length
        s.append(script)
        s.append("ffffffff")                                        # sequence
        return ''.join(s)

    def serialize_output(self, output, for_sig=None):
        s = []
        type, addr, amount = output
        s.append(int_to_hex( amount, 8))                            # amount
        script = self.pay_script(type, addr)
        s.append(var_int( len(script)/2 ))                          #  script length
        s.append(script)                                            #  script
        return ''.join(s)

    def serialize(self, for_sig=None):
        """Serialize transaction as a hex-encoded string.

        Args: for_sig: If this serialization is for signing.
                Has the following possible values:

                - -1    : do not sign, estimate length
                - >=0   : serialized tx for signing input i
                - None  : add all known signatures
        """
        inputs = self.inputs
        outputs = self.outputs

        # field, field data(data_overridden_by_chainhook)
        fields = [('version', []),
                ('vin', []),
                ('inputs', []),
                ('vout', []),
                ('outputs', []),
                ('locktime', []),
                ('hashtype', [])
                ]
        run_chainhook('transaction_serialize', self, for_sig, fields)
        for i, (field, field_data) in enumerate(fields):
            if not field_data:
                if field == 'version':
                    field_data.append(int_to_hex(1,4))
                elif field == 'vin':
                    field_data.append(var_int(len(inputs)))
                elif field == 'inputs':
                    for i in range(len(inputs)):
                        field_data.append(self.serialize_input(i, for_sig))
                elif field == 'vout':
                    field_data.append(var_int(len(outputs)))
                elif field == 'outputs':
                    for output in outputs:
                        field_data.append(self.serialize_output(output, for_sig))
                elif field == 'locktime':
                    field_data.append(int_to_hex(0,4))
                elif field == 'hashtype':
                    if for_sig is not None and for_sig != -1:
                        field_data.append(int_to_hex(1,4))
        s = []
        for field, field_data in fields:
            s.append(''.join(field_data))

        return ''.join(s)

    def tx_for_sig(self,i):
        return self.serialize(for_sig = i)

    def hash(self):
        return hashes.transaction_hash(self.raw.decode('hex') )[::-1].encode('hex')

    def add_input(self, input):
        self.inputs.append(input)
        self.raw = None

    def input_value(self):
        return sum([x['value'] for x in self.inputs])

    def output_value(self):
        return sum([ x[2] for x in self.outputs])

    def get_fee(self):
        return self.input_value() - self.output_value()

    def signature_count(self):
        r = 0
        s = 0
        for txin in self.inputs:
            if txin.get('is_coinbase'):
                continue
            signatures = filter(lambda x: x is not None, txin['signatures'])
            s += len(signatures)
            r += txin['num_sig']
        return s, r

    def is_complete(self):
        s, r = self.signature_count()
        return r == s

    def inputs_to_sign(self):
        out = set()
        for txin in self.inputs:
            x_signatures = txin['signatures']
            signatures = filter(lambda x: x is not None, x_signatures)
            if len(signatures) == txin['num_sig']:
                # input is complete
                continue
            for k, x_pubkey in enumerate(txin['x_pubkeys']):
                if x_signatures[k] is not None:
                    # this pubkey already signed
                    continue
                out.add(x_pubkey)
        return out

    def sign(self, keypairs):
        """Signs inputs that keypairs can sign.

        Args:
            keypairs (dict): {public key in hex : private key in WIF, ...}

        """
        print_error("tx.sign(), keypairs:", keypairs)
        for i, txin in enumerate(self.inputs):
            signatures = filter(lambda x: x is not None, txin['signatures'])
            num = txin['num_sig']
            if len(signatures) == num:
                # continue if this txin is complete
                continue

            for x_pubkey in txin['x_pubkeys']:
                if x_pubkey in keypairs.keys():
                    print_error("adding signature for", x_pubkey)
                    # add pubkey to txin
                    txin = self.inputs[i]
                    x_pubkeys = txin['x_pubkeys']
                    ii = x_pubkeys.index(x_pubkey)
                    sec = keypairs[x_pubkey]
                    pubkey = public_key_from_private_key(sec, self.active_chain.wif_version)
                    txin['x_pubkeys'][ii] = pubkey
                    txin['pubkeys'][ii] = pubkey
                    self.inputs[i] = txin
                    # add signature
                    for_sig = hashes.transaction_hash(self.tx_for_sig(i).decode('hex'))
                    pkey = regenerate_key(sec, self.active_chain.wif_version)
                    secexp = pkey.secret
                    private_key = ecdsa.SigningKey.from_secret_exponent( secexp, curve = SECP256k1 )
                    public_key = private_key.get_verifying_key()
                    sig = private_key.sign_digest_deterministic( for_sig, hashfunc=hashlib.sha256, sigencode = ecdsa.util.sigencode_der_canonize )
                    assert public_key.verify_digest( sig, for_sig, sigdecode = ecdsa.util.sigdecode_der)
                    txin['signatures'][ii] = sig.encode('hex')
                    self.inputs[i] = txin

        print_error("is_complete", self.is_complete())
        self.raw = self.serialize()


    def add_pubkey_addresses(self, txlist):
        for i in self.inputs:
            if i.get("address") == "(pubkey)":
                prev_tx = txlist.get(i.get('prevout_hash'))
                if prev_tx:
                    address, value = prev_tx.get_outputs()[i.get('prevout_n')]
                    print_error("found pay-to-pubkey address:", address)
                    i["address"] = address


    def get_outputs(self):
        """convert pubkeys to addresses"""
        o = []
        for type, x, v in self.outputs:
            if type == 'address':
                addr = x
            elif type == 'pubkey':
                addr = public_key_to_bc_address(x.decode('hex'), self.active_chain.p2pkh_version)
            elif type == 'op_return':
                try:
                    addr = 'OP_RETURN: "' + x.decode('utf8') + '"'
                except:
                    addr = 'OP_RETURN: "' + x.encode('hex') + '"'
            else:
                addr = "(None)"
            o.append((addr,v))
        return o

    def get_output_addresses(self):
        return map(lambda x:x[0], self.get_outputs())


    def has_address(self, addr):
        found = False
        for txin in self.inputs:
            if addr == txin.get('address'):
                found = True
                break
        if addr in self.get_output_addresses():
            found = True

        return found


    def get_value(self, addresses, prevout_values):
        # return the balance for that tx
        is_relevant = False
        is_send = False
        is_pruned = False
        is_partial = False
        v_in = v_out = v_out_mine = 0

        for item in self.inputs:
            addr = item.get('address')
            if addr in addresses:
                is_send = True
                is_relevant = True
                key = item['prevout_hash']  + ':%d'%item['prevout_n']
                value = prevout_values.get( key )
                if value is None:
                    is_pruned = True
                else:
                    v_in += value
            else:
                is_partial = True

        if not is_send: is_partial = False

        for addr, value in self.get_outputs():
            v_out += value
            if addr in addresses:
                v_out_mine += value
                is_relevant = True

        if is_pruned:
            # some inputs are mine:
            fee = None
            if is_send:
                v = v_out_mine - v_out
            else:
                # no input is mine
                v = v_out_mine

        else:
            v = v_out_mine - v_in

            if is_partial:
                # some inputs are mine, but not all
                fee = None
                is_send = v < 0
            else:
                # all inputs are mine
                fee = v_out - v_in

        return is_relevant, is_send, v, fee


    def as_dict(self):
        import json
        out = {
            "hex":str(self),
            "complete":self.is_complete()
            }
        return out


    def requires_fee(self, verifier):
        # see https://en.bitcoin.it/wiki/Transaction_fees
        threshold = 57600000
        size = len(self.serialize(-1))/2
        if size >= 10000:
            return True

        for o in self.get_outputs():
            value = o[1]
            if value < 1000000:
                return True
        sum = 0
        for i in self.inputs:
            age = verifier.get_confirmations(i["prevout_hash"])[0]
            sum += i["value"] * age
        priority = sum / size
        print_error(priority, threshold)
        return priority < threshold

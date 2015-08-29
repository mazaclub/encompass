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

import sys
import os
import hashlib
import ast
import threading
import random
import time
import math
import json
import copy
import chainparams

from util import print_msg, print_error

from bitcoin import *
from eckey import pw_encode, pw_decode
from account import *
from version import *
import base58

from transaction import Transaction
from plugins import run_hook
import bitcoin
from synchronizer import WalletSynchronizer
from mnemonic import Mnemonic
from simple_config import SimpleConfig



# internal ID for imported account
IMPORTED_ACCOUNT = '/x'


class WalletStorage(object):

    def __init__(self, config):
        self.lock = threading.RLock()
        if not isinstance(config, SimpleConfig):
            dormant = config.get('dormant')
            if dormant is None: dormant = False
            config = SimpleConfig(config, dormant=dormant)
        self.config = config
        self.dormant = config.dormant
        self.data = {}
        self.file_exists = False
        self.path = config.get_wallet_path()
        print_error( "wallet path", self.path )
        if self.path:
            self.read(self.path)
        self._init_chains()

    def _init_chains(self):
        """Make sure there's a dictionary for each chain"""
        for code in chainparams.known_chain_codes:
            if self.get_above_chain(code, None) is None:
                self.put_above_chain(code, {})

    def read(self, path):
        """Read the contents of the wallet file."""
        try:
            with open(self.path, "r") as f:
                data = f.read()
        except IOError:
            return
        try:
            self.data = json.loads(data)
        except:
            try:
                d = ast.literal_eval(data)  #parse raw data from reading wallet file
            except Exception:
                raise IOError("Cannot read wallet file.")
            self.data = {}
            for key, value in d.items():
                try:
                    json.dumps(key)
                    json.dumps(value)
                except:
                    continue
                self.data[key] = value
        self.file_exists = True

    def get_above_chain(self, key, default=None):
        with self.lock:
            v = self.data.get(key)
            if v is None:
                v = default
            else:
                v = copy.deepcopy(v)
            return v

    def get_chain_value(self, code, key, default=None):
        """Shortcut for getting info within a certain chain"""
        try:
            chain = self.get_above_chain(code)
            data = chain.get(key)
        except:
            data = None
        return data

    def set_chain_value(self, code, key, value):
        """Shortcut for setting info within a certain chain"""
        try:
            json.dumps(key)
            json.dumps(value)
            chain = self.get_above_chain(code)
        except:
            return
        with self.lock:
            if value is not None and chain is not None:
                self.data[code][key] = copy.deepcopy(value)
                self.write()

    def get(self, key, default=None):
        active_chain_code = self.config.get_active_chain_code()
        if active_chain_code is None:
            active_chain_code = chainparams.get_active_chain().code
        with self.lock:
            v = self.data[active_chain_code].get(key)
            if v is None:
                v = default
            else:
                v = copy.deepcopy(v)
            return v

    def put_above_chain(self, key, value, save = True):
        '''Bypass the usual practice of storing something in the active chain's dict'''
        try:
            json.dumps(key)
            json.dumps(value)
        except:
            print_error("json error: cannot save", key)
            return
        with self.lock:
            if value is not None:
                self.data[key] = copy.deepcopy(value)
            elif key in self.data:
                self.data.pop(key)
            if save:
                self.write()

    def put(self, key, value, save = True):
        try:
            json.dumps(key)
            json.dumps(value)
        except:
            print_error("json error: cannot save", key)

        active_chain_code = self.config.get_active_chain_code()
        if active_chain_code is None:
            active_chain_code = chainparams.get_active_chain().code
        with self.lock:
            if value is not None:
                self.data[active_chain_code][key] = copy.deepcopy(value)
            elif key in self.data[active_chain_code]:
                self.data[active_chain_code].pop(key)
            if save:
                self.write()

    def write(self):
        if self.dormant: return
        s = json.dumps(self.data, indent=4, sort_keys=True)
        f = open(self.path,"w")
        f.write(s)
        f.close()
        if 'ANDROID_DATA' not in os.environ:
            import stat
            os.chmod(self.path,stat.S_IREAD | stat.S_IWRITE)


class Abstract_Wallet(object):
    """
    Wallet classes are created to handle various address generation methods.
    Completion states (watching-only, single account, no seed, etc) are handled inside classes.
    """
    def __init__(self, storage):
        self.storage = storage
        self.electrum_version = ELECTRUM_VERSION
        self.gap_limit_for_change = 3 # constant
        # saved fields
        self.active_chain_code     = storage.config.get_active_chain_code()
        if self.active_chain_code is None:
            self.active_chain_code = chainparams.get_active_chain().code
        self.active_chain          = chainparams.get_chain_instance(self.active_chain_code)
        self.seed_version          = storage.get_above_chain('seed_version', NEW_SEED_VERSION)
        self.use_change            = storage.get('use_change',True)
        self.use_encryption        = storage.get_above_chain('use_encryption', False)
        self.seed                  = storage.get_above_chain('seed', '')               # encrypted
        self.labels                = storage.get('labels', {})
        self.frozen_addresses      = storage.get('frozen_addresses',[])
        self.addressbook           = storage.get('contacts', [])

        self.history               = storage.get('addr_history',{})        # address -> list(txid, height)
        self.fee_per_kb            = int(storage.get('fee_per_kb', self.active_chain.RECOMMENDED_FEE))

        # This attribute is set when wallet.start_threads is called.
        self.synchronizer = None

        # imported_keys is deprecated. The GUI should call convert_imported_keys
        self.imported_keys = self.storage.get('imported_keys',{})

        self.load_accounts()

        self.load_transactions()

        # not saved
        self.prevout_values = {}     # my own transaction outputs
        self.spent_outputs = []
        # spv
        self.verifier = None
        # there is a difference between wallet.up_to_date and interface.is_up_to_date()
        # interface.is_up_to_date() returns true when all requests have been answered and processed
        # wallet.up_to_date is true when the wallet is synchronized (stronger requirement)
        self.up_to_date = False
        self.lock = threading.Lock()
        self.transaction_lock = threading.Lock()
        self.tx_event = threading.Event()
        for tx_hash, tx in self.transactions.items():
            self.update_tx_outputs(tx_hash)

        # save wallet type the first time
        if self.storage.get_above_chain('wallet_type') is None:
            self.storage.put_above_chain('wallet_type', self.wallet_type, True)
        #if self.storage.get('wallet_type') is None:
        #    self.storage.put('wallet_type', self.wallet_type, True)

    def set_chain(self, chaincode):
        result = self.storage.config.set_active_chain_code(chaincode)
        if result == False:
            return False # Invalid chain
        self.__init__(self.storage)
        return True

    def load_transactions(self):
        self.transactions = {}
        tx_list = self.storage.get('transactions',{})
        for k, raw in tx_list.items():
            try:
                tx = Transaction.deserialize(raw, self.active_chain)
            except Exception:
                print_msg("Warning: Cannot deserialize transactions. skipping")
                continue
            self.add_pubkey_addresses(tx)
            self.transactions[k] = tx
        for h,tx in self.transactions.items():
            if not self.check_new_tx(h, tx):
                print_error("removing unreferenced tx", h)
                self.transactions.pop(h)

    def add_pubkey_addresses(self, tx):
        # find the address corresponding to pay-to-pubkey inputs
        h = tx.hash()

        # inputs
        tx.add_pubkey_addresses(self.transactions)

        # outputs of tx: inputs of tx2
        for type, x, v in tx.outputs:
            if type == 'pubkey':
                for tx2 in self.transactions.values():
                    tx2.chain = self.active_chain
                    tx2.add_pubkey_addresses({h:tx})

    def get_action(self):
        pass

    def convert_imported_keys(self, password):
        for k, v in self.imported_keys.items():
            sec = pw_decode(v, password)
            pubkey = public_key_from_private_key(sec, self.active_chain.wif_version)
            address = public_key_to_bc_address(pubkey.decode('hex'), addrtype=self.active_chain.p2pkh_version)
            assert address == k
            self.import_key(sec, password)
            self.imported_keys.pop(k)
        self.storage.put('imported_keys', self.imported_keys)

    def load_accounts(self):
        self.accounts = {}

        d = self.storage.get('accounts', {})
        for k, v in d.items():
            if self.wallet_type == 'old' and k in [0, '0']:
                v['mpk'] = self.storage.get('master_public_key')
                self.accounts[k] = OldAccount(v)
            elif v.get('imported'):
                self.accounts[k] = ImportedAccount(v)
            elif v.get('cosigner_xpubs'):
                self.accounts[k] = BIP32_Account_MofN(v)
            elif v.get('xpub3'):
                self.accounts[k] = BIP32_Account_2of3(v)
            elif v.get('xpub2'):
                self.accounts[k] = BIP32_Account_2of2(v)
            elif v.get('xpub'):
                self.accounts[k] = BIP32_Account(v)
            elif v.get('pending'):
                self.accounts[k] = PendingAccount(v)
            else:
                print_error("cannot load account", v)

    def synchronize(self):
        pass

    def can_create_accounts(self):
        return False

    def set_up_to_date(self,b):
        with self.lock: self.up_to_date = b

    def is_up_to_date(self):
        with self.lock: return self.up_to_date

    def update(self):
        self.up_to_date = False
        while not self.is_up_to_date():
            time.sleep(0.1)

    def is_imported(self, addr):
        account = self.accounts.get(IMPORTED_ACCOUNT)
        if account:
            return addr in account.get_addresses(0)
        else:
            return False

    def has_imported_keys(self):
        account = self.accounts.get(IMPORTED_ACCOUNT)
        return account is not None

    def import_key(self, sec, password):
        try:
            pubkey = public_key_from_private_key(sec, self.active_chain.wif_version)
            address = public_key_to_bc_address(pubkey.decode('hex'), addrtype=self.active_chain.p2pkh_version)
        except Exception:
            raise Exception('Invalid private key')

        if self.is_mine(address):
            raise Exception('Address already in wallet')

        if self.accounts.get(IMPORTED_ACCOUNT) is None:
            self.accounts[IMPORTED_ACCOUNT] = ImportedAccount({'imported':{}})
        self.accounts[IMPORTED_ACCOUNT].add(address, pubkey, sec, password)
        self.save_accounts()

        if self.synchronizer:
            self.synchronizer.add(address)
        return address

    def delete_imported_key(self, addr):
        account = self.accounts[IMPORTED_ACCOUNT]
        account.remove(addr)
        if not account.get_addresses(0):
            self.accounts.pop(IMPORTED_ACCOUNT)
        self.save_accounts()

    def set_label(self, name, text = None):
        changed = False
        old_text = self.labels.get(name)
        if text:
            if old_text != text:
                self.labels[name] = text
                changed = True
        else:
            if old_text:
                self.labels.pop(name)
                changed = True

        if changed:
            self.storage.put('labels', self.labels, True)

        run_hook('set_label', name, text, changed)
        return changed

    def addresses(self, include_change = True):
        o = []
        for a in self.accounts.keys():
            o += self.get_account_addresses(a, include_change)
        return o

    def is_mine(self, address):
        return address in self.addresses(True)

    def is_change(self, address):
        if not self.is_mine(address): return False
        acct, s = self.get_address_index(address)
        if s is None: return False
        return s[0] == 1

    def get_address_index(self, address):
        for account in self.accounts.keys():
            for for_change in [0,1]:
                addresses = self.accounts[account].get_addresses(for_change)
                for addr in addresses:
                    if address == addr:
                        return account, (for_change, addresses.index(addr))
        raise Exception("Address not found", address)

    def get_private_key(self, address, password):
        if self.is_watching_only():
            return []
        account_id, sequence = self.get_address_index(address)
        return self.accounts[account_id].get_private_key(sequence, self, password)

    def get_public_keys(self, address):
        account_id, sequence = self.get_address_index(address)
        return self.accounts[account_id].get_pubkeys(*sequence)


    def sign_message(self, address, message, password):
        keys = self.get_private_key(address, password)
        assert len(keys) == 1
        sec = keys[0]
        key = regenerate_key(sec, self.active_chain.wif_version)
        compressed = is_compressed(sec)
        return key.sign_message(message, compressed, address)

    def decrypt_message(self, pubkey, message, password):
        address = public_key_to_bc_address(pubkey.decode('hex'), self.active_chain.p2pkh_version)
        keys = self.get_private_key(address, password)
        secret = keys[0]
        ec = regenerate_key(secret, self.active_chain.wif_version)
        decrypted = ec.decrypt_message(message)
        return decrypted

    def is_found(self):
        return self.history.values() != [[]] * len(self.history)

    def add_contact(self, address, label=None):
        self.addressbook.append(address)
        self.storage.put('contacts', self.addressbook, True)
        if label:
            self.set_label(address, label)

    def delete_contact(self, addr):
        if addr in self.addressbook:
            self.addressbook.remove(addr)
            self.storage.put('addressbook', self.addressbook, True)

    def fill_addressbook(self):
        for tx_hash, tx in self.transactions.items():
            is_relevant, is_send, _, _ = self.get_tx_value(tx)
            if is_send:
                for addr in tx.get_output_addresses():
                    if not self.is_mine(addr) and addr not in self.addressbook:
                        self.addressbook.append(addr)
        # redo labels
        # self.update_tx_labels()

    def get_num_tx(self, address):
        n = 0
        for tx in self.transactions.values():
            if address in tx.get_output_addresses(): n += 1
        return n

    def get_tx_value(self, tx, account=None):
        domain = self.get_account_addresses(account)
        return tx.get_value(domain, self.prevout_values)

    def update_tx_outputs(self, tx_hash):
        tx = self.transactions.get(tx_hash)

        for i, (addr, value) in enumerate(tx.get_outputs()):
            key = tx_hash+ ':%d'%i
            self.prevout_values[key] = value

        for item in tx.inputs:
            if self.is_mine(item.get('address')):
                key = item['prevout_hash'] + ':%d'%item['prevout_n']
                self.spent_outputs.append(key)

    def get_addr_balance(self, address):
        #assert self.is_mine(address)
        h = self.history.get(address,[])
        if h == ['*']: return 0,0
        c = u = 0
        received_coins = []   # list of coins received at address

        for tx_hash, tx_height in h:
            tx = self.transactions.get(tx_hash)
            if not tx: continue

            for i, (addr, value) in enumerate(tx.get_outputs()):
                if addr == address:
                    key = tx_hash + ':%d'%i
                    received_coins.append(key)

        for tx_hash, tx_height in h:
            tx = self.transactions.get(tx_hash)
            if not tx: continue
            v = 0

            for item in tx.inputs:
                addr = item.get('address')
                if addr == address:
                    key = item['prevout_hash']  + ':%d'%item['prevout_n']
                    value = self.prevout_values.get( key )
                    if key in received_coins:
                        v -= value

            for i, (addr, value) in enumerate(tx.get_outputs()):
                key = tx_hash + ':%d'%i
                if addr == address:
                    v += value

            if tx_height:
                c += v
            else:
                u += v
        return c, u

    def get_account_name(self, k):
        return self.labels.get(k, self.accounts[k].get_name(k))

    def get_account_names(self):
        account_names = {}
        for k in self.accounts.keys():
            account_names[k] = self.get_account_name(k)
        return account_names

    def get_account_addresses(self, a, include_change=True):
        if a is None:
            o = self.addresses(include_change)
        elif a in self.accounts:
            ac = self.accounts[a]
            o = ac.get_addresses(0)
            if include_change: o += ac.get_addresses(1)
        return o

    def get_account_balance(self, account):
        return self.get_balance(self.get_account_addresses(account))

    def get_frozen_balance(self):
        return self.get_balance(self.frozen_addresses)

    def get_balance(self, domain=None):
        if domain is None: domain = self.addresses(True)
        cc = uu = 0
        for addr in domain:
            c, u = self.get_addr_balance(addr)
            cc += c
            uu += u
        return cc, uu

    def get_unspent_coins(self, domain=None):
        coins = []
        if domain is None: domain = self.addresses(True)
        for addr in domain:
            h = self.history.get(addr, [])
            if h == ['*']: continue
            for tx_hash, tx_height in h:
                tx = self.transactions.get(tx_hash)
                if tx is None: raise Exception("Wallet not synchronized")
                is_coinbase = tx.inputs[0].get('prevout_hash') == '0'*64
                for i, (address, value) in enumerate(tx.get_outputs()):
                    output = {'address':address, 'value':value, 'prevout_n':i}
                    if address != addr: continue
                    key = tx_hash + ":%d"%i
                    if key in self.spent_outputs: continue
                    output['prevout_hash'] = tx_hash
                    output['height'] = tx_height
                    output['coinbase'] = is_coinbase
                    coins.append((tx_height, output))

        # sort by age
        if coins:
            coins = sorted(coins)
            if coins[-1][0] != 0:
                while coins[0][0] == 0:
                    coins = coins[1:] + [ coins[0] ]
        return [x[1] for x in coins]



    def set_fee(self, fee):
        if self.fee_per_kb != fee:
            self.fee_per_kb = fee
            self.storage.put('fee_per_kb', self.fee_per_kb, True)


    def get_history(self, address):
        with self.lock:
            return self.history.get(address)

    def get_status(self, h):
        if not h: return None
        if h == ['*']: return '*'
        status = ''
        for tx_hash, height in h:
            status += tx_hash + ':%d:' % height
        return hashlib.sha256( status ).digest().encode('hex')

    def receive_tx_callback(self, tx_hash, tx, tx_height):

        with self.transaction_lock:
            self.add_pubkey_addresses(tx)
            if not self.check_new_tx(tx_hash, tx):
                # may happen due to pruning
                print_error("received transaction that is no longer referenced in history", tx_hash)
                return
            self.transactions[tx_hash] = tx
            self.network.pending_transactions_for_notifications.append(tx)
            self.save_transactions()
            if self.verifier and tx_height>0:
                self.verifier.add(tx_hash, tx_height)
            self.update_tx_outputs(tx_hash)
        run_hook('receive_tx_callback', tx_hash, tx, tx_height)

    def save_transactions(self):
        tx = {}
        for k,v in self.transactions.items():
            tx[k] = str(v)
        self.storage.put('transactions', tx, True)

    def receive_history_callback(self, addr, hist):

        if not self.check_new_history(addr, hist):
            raise Exception("error: received history for %s is not consistent with known transactions"%addr)

        with self.lock:
            self.history[addr] = hist
            self.storage.put('addr_history', self.history, True)

        if hist != ['*']:
            for tx_hash, tx_height in hist:
                if tx_height>0:
                    # add it in case it was previously unconfirmed
                    if self.verifier: self.verifier.add(tx_hash, tx_height)

    def get_tx_history(self, account=None):
        if not self.verifier:
            return []

        with self.transaction_lock:
            history = self.transactions.items()
            history.sort(key = lambda x: self.verifier.get_txpos(x[0]))
            result = []

            balance = 0
            for tx_hash, tx in history:
                is_relevant, is_mine, v, fee = self.get_tx_value(tx, account)
                if v is not None: balance += v

            c, u = self.get_account_balance(account)

            if balance != c+u:
                result.append( ('', 1000, 0, c+u-balance, None, c+u-balance, None ) )

            balance = c + u - balance
            for tx_hash, tx in history:
                is_relevant, is_mine, value, fee = self.get_tx_value(tx, account)
                if not is_relevant:
                    continue
                if value is not None:
                    balance += value

                conf, timestamp = self.verifier.get_confirmations(tx_hash) if self.verifier else (None, None)
                result.append( (tx_hash, conf, is_mine, value, fee, balance, timestamp) )

        return result

    def get_label(self, tx_hash):
        label = self.labels.get(tx_hash)
        is_default = (label == '') or (label is None)
        if is_default: label = self.get_default_label(tx_hash)
        return label, is_default

    def get_default_label(self, tx_hash):
        tx = self.transactions.get(tx_hash)
        default_label = ''
        if tx:
            is_relevant, is_mine, _, _ = self.get_tx_value(tx)
            if is_mine:
                for o_addr in tx.get_output_addresses():
                    if not self.is_mine(o_addr):
                        try:
                            default_label = self.labels[o_addr]
                        except KeyError:
                            default_label = ''.join([ '>', o_addr ])
                        break
                else:
                    default_label = '(internal)'
                    if len(self.accounts) > 1:
                        # find input account and output account
                        i_addr = tx.inputs[0]["address"]
                        i_acc,_ = self.get_address_index(i_addr)
                        for o_addr in tx.get_output_addresses():
                            o_acc,_ = self.get_address_index(o_addr)
                            if o_acc != i_acc:
                                default_label = '(internal: %s --> %s)'%(self.get_account_name(i_acc),self.get_account_name(o_acc))
                                break

            else:
                for o_addr in tx.get_output_addresses():
                    if self.is_mine(o_addr) and not self.is_change(o_addr):
                        break
                else:
                    for o_addr in tx.get_output_addresses():
                        if self.is_mine(o_addr):
                            break
                    else:
                        o_addr = None

                if o_addr:
                    try:
                        default_label = self.labels[o_addr]
                    except KeyError:
                        default_label = ''.join([ '<', o_addr ])

        default_label = ''.join([ default_label, ' [{}...]'.format(tx_hash[0:8]) ])
        return default_label

    def get_tx_fee(self, tx):
        # this method can be overloaded
        return tx.get_fee()

    def estimated_fee(self, tx):
        estimated_size = len(tx.serialize(-1))/2
        fee = int(self.fee_per_kb*estimated_size/1000.)
        if fee < self.active_chain.MIN_RELAY_TX_FEE: # and tx.requires_fee(self.verifier):
            fee = self.active_chain.MIN_RELAY_TX_FEE
        return fee

    def make_unsigned_transaction(self, outputs, fixed_fee=None, change_addr=None, domain=None, coins=None ):
        # check outputs
        for type, data, value in outputs:
            if type == 'op_return':
                assert len(data) < 41, "string too long"
                #assert value == 0
            if type == 'address':
                assert is_address(data), "Address " + data + " is invalid!"

        # get coins
        if not coins:
            if domain is None:
                domain = self.addresses(True)
            for i in self.frozen_addresses:
                if i in domain: domain.remove(i)
            coins = self.get_unspent_coins(domain)

        amount = sum( map(lambda x:x[2], outputs) )
        total = fee = 0
        inputs = []
        tx = Transaction(inputs, outputs)
        for item in coins:
            if item.get('coinbase') and item.get('height') + self.active_chain.COINBASE_MATURITY > self.network.get_local_height():
                continue
            v = item.get('value')
            total += v
            self.add_input_info(item)
            tx.add_input(item)
            fee = fixed_fee if fixed_fee is not None else self.estimated_fee(tx)
            if total >= amount + fee: break
        else:
            print_error("Not enough funds", total, amount, fee)
            return None

        # change address
        if not change_addr:
            # send change to one of the accounts involved in the tx
            address = inputs[0].get('address')
            account, _ = self.get_address_index(address)
            if not self.use_change or account == IMPORTED_ACCOUNT:
                change_addr = address
            else:
                change_addr = self.accounts[account].get_addresses(1)[-self.gap_limit_for_change]

        # if change is above dust threshold, add a change output.
        change_amount = total - ( amount + fee )
        if fixed_fee is not None and change_amount > 0:
            # Insert the change output at a random position in the outputs
            posn = random.randint(0, len(tx.outputs))
            tx.outputs[posn:posn] = [( 'address', change_addr,  change_amount)]
        elif change_amount > self.active_chain.DUST_THRESHOLD:
            # Insert the change output at a random position in the outputs
            posn = random.randint(0, len(tx.outputs))
            tx.outputs[posn:posn] = [( 'address', change_addr,  change_amount)]
            # recompute fee including change output
            fee = self.estimated_fee(tx)
            # remove change output
            tx.outputs.pop(posn)
            # if change is still above dust threshold, re-add change output.
            change_amount = total - ( amount + fee )
            if change_amount > self.active_chain.DUST_THRESHOLD:
                tx.outputs[posn:posn] = [( 'address', change_addr,  change_amount)]
                print_error('change', change_amount)
            else:
                print_error('not keeping dust', change_amount)
        else:
            print_error('not keeping dust', change_amount)

        run_hook('make_unsigned_transaction', tx)
        return tx

    def mktx(self, outputs, password, fee=None, change_addr=None, domain= None, coins = None ):
        tx = self.make_unsigned_transaction(outputs, fee, change_addr, domain, coins)
        self.sign_transaction(tx, password)
        return tx

    def add_input_info(self, txin):
        address = txin['address']
        account_id, sequence = self.get_address_index(address)
        account = self.accounts[account_id]
        redeemScript = account.redeem_script(*sequence)
        pubkeys = account.get_pubkeys(*sequence)
        x_pubkeys = account.get_xpubkeys(*sequence)
        # sort pubkeys and x_pubkeys, using the order of pubkeys
        pubkeys, x_pubkeys = zip( *sorted(zip(pubkeys, x_pubkeys)))
        txin['pubkeys'] = list(pubkeys)
        txin['x_pubkeys'] = list(x_pubkeys)
        txin['signatures'] = [None] * len(pubkeys)

        if redeemScript:
            txin['redeemScript'] = redeemScript
            m = 2
            acc_type = str(account.get_type())
            if 'M of N' in acc_type:
                m = account.multisig_m
            txin['num_sig'] = m
        else:
            txin['redeemPubkey'] = account.get_pubkey(*sequence)
            txin['num_sig'] = 1

    def sign_transaction(self, tx, password):
        if self.is_watching_only():
            return
        # check that the password is correct. This will raise if it's not.
        self.check_password(password)
        keypairs = {}
        x_pubkeys = tx.inputs_to_sign()
        for x in x_pubkeys:
            if not self.can_sign_xpubkey(x):
                continue
            sec = self.get_private_key_from_xpubkey(x, password)
            print "sec", sec
            if sec:
                keypairs[ x ] = sec
        if keypairs:
            tx.sign(keypairs)
        run_hook('sign_transaction', tx, password)

    def sendtx(self, tx):
        # synchronous
        h = self.send_tx(tx)
        self.tx_event.wait()
        return self.receive_tx(h, tx)

    def send_tx(self, tx):
        # asynchronous
        self.tx_event.clear()
        self.network.send([('blockchain.transaction.broadcast', [str(tx)])], self.on_broadcast)
        return tx.hash()

    def on_broadcast(self, r):
        self.tx_result = r.get('result')
        self.tx_event.set()

    def receive_tx(self, tx_hash, tx):
        out = self.tx_result
        if out != tx_hash:
            return False, "error: " + out
        run_hook('receive_tx', tx, self)
        return True, out

    def update_password(self, old_password, new_password):
        if new_password == '':
            new_password = None

        if self.has_seed():
            decoded = self.get_seed(old_password)
            self.seed = pw_encode( decoded, new_password)
            self.storage.put_above_chain('seed', self.seed, True)

        imported_account = self.accounts.get(IMPORTED_ACCOUNT)
        if imported_account:
            imported_account.update_password(old_password, new_password)
            self.save_accounts()

        # loop through chains an re-encrypt private keys
        chaincodes = chainparams.known_chain_codes
        for code in chaincodes:
            # skip the active chain
            if code == self.active_chain.code: continue
            chain = self.storage.get_above_chain(code)
            master_keys = chain.get('master_private_keys', None)
            if master_keys is None: continue
            for k, v in master_keys.items():
                old = pw_decode(v, old_password)
                new = pw_encode(old, new_password)
                chain['master_private_keys'][k] = new
            self.storage.put_above_chain(code, chain)

        if hasattr(self, 'master_private_keys'):
            for k, v in self.master_private_keys.items():
                b = pw_decode(v, old_password)
                c = pw_encode(b, new_password)
                self.master_private_keys[k] = c
            self.storage.put('master_private_keys', self.master_private_keys, True)

        self.use_encryption = (new_password != None)
        self.storage.put_above_chain('use_encryption', self.use_encryption,True)

    def freeze(self,addr):
        if self.is_mine(addr) and addr not in self.frozen_addresses:
            self.frozen_addresses.append(addr)
            self.storage.put('frozen_addresses', self.frozen_addresses, True)
            return True
        else:
            return False

    def unfreeze(self,addr):
        if self.is_mine(addr) and addr in self.frozen_addresses:
            self.frozen_addresses.remove(addr)
            self.storage.put('frozen_addresses', self.frozen_addresses, True)
            return True
        else:
            return False

    def set_verifier(self, verifier):
        self.verifier = verifier

        # review transactions that are in the history
        for addr, hist in self.history.items():
            if hist == ['*']: continue
            for tx_hash, tx_height in hist:
                if tx_height>0:
                    # add it in case it was previously unconfirmed
                    self.verifier.add(tx_hash, tx_height)

        # if we are on a pruning server, remove unverified transactions
        vr = self.verifier.transactions.keys() + self.verifier.verified_tx.keys()
        for tx_hash in self.transactions.keys():
            if tx_hash not in vr:
                self.transactions.pop(tx_hash)

    def check_new_history(self, addr, hist):
        # check that all tx in hist are relevant
        if hist != ['*']:
            for tx_hash, height in hist:
                tx = self.transactions.get(tx_hash)
                if not tx: continue
                if not tx.has_address(addr):
                    return False

        # check that we are not "orphaning" a transaction
        old_hist = self.history.get(addr,[])
        if old_hist == ['*']: return True

        for tx_hash, height in old_hist:
            if tx_hash in map(lambda x:x[0], hist): continue
            found = False
            for _addr, _hist in self.history.items():
                if _addr == addr: continue
                if _hist == ['*']: continue
                _tx_hist = map(lambda x:x[0], _hist)
                if tx_hash in _tx_hist:
                    found = True
                    break

            if not found:
                tx = self.transactions.get(tx_hash)
                # tx might not be there
                if not tx: continue

                # already verified?
                if self.verifier.get_height(tx_hash):
                    continue
                # unconfirmed tx
                print_error("new history is orphaning transaction:", tx_hash)
                # check that all outputs are not mine, request histories
                ext_requests = []
                for _addr in tx.get_output_addresses():
                    # assert not self.is_mine(_addr)
                    ext_requests.append( ('blockchain.address.get_history', [_addr]) )

                ext_h = self.network.synchronous_get(ext_requests)
                print_error("sync:", ext_requests, ext_h)
                height = None
                for h in ext_h:
                    if h == ['*']: continue
                    for item in h:
                        if item.get('tx_hash') == tx_hash:
                            height = item.get('height')
                if height:
                    print_error("found height for", tx_hash, height)
                    self.verifier.add(tx_hash, height)
                else:
                    print_error("removing orphaned tx from history", tx_hash)
                    self.transactions.pop(tx_hash)

        return True

    def check_new_tx(self, tx_hash, tx):
        # 1 check that tx is referenced in addr_history.
        addresses = []
        for addr, hist in self.history.items():
            if hist == ['*']:continue
            for txh, height in hist:
                if txh == tx_hash:
                    addresses.append(addr)

        if not addresses:
            return False

        # 2 check that referencing addresses are in the tx
        for addr in addresses:
            if not tx.has_address(addr):
                return False

        return True

    def start_threads(self, network):
        from verifier import TxVerifier
        self.network = network
        if self.network is not None:
            self.verifier = TxVerifier(self.network, self.storage)
            self.verifier.start()
            self.set_verifier(self.verifier)
            self.synchronizer = WalletSynchronizer(self, network)
            self.synchronizer.start()
        else:
            self.verifier = None
            self.synchronizer =None

    def stop_threads(self):
        if self.network:
            if self.verifier:
                self.verifier.stop()
            if self.synchronizer:
                self.synchronizer.stop()

    def restore(self, cb):
        pass

    def get_accounts(self):
        return self.accounts

    def add_account(self, account_id, account):
        self.accounts[account_id] = account
        self.save_accounts()

    def save_accounts(self):
        d = {}
        for k, v in self.accounts.items():
            d[k] = v.dump()
        self.storage.put('accounts', d, True)

    def can_import(self):
        return not self.is_watching_only()

    def can_export(self):
        return not self.is_watching_only()

    def is_used(self, address):
        h = self.history.get(address,[])
        c, u = self.get_addr_balance(address)
        return len(h), len(h) > 0 and c == -u

    def address_is_old(self, address, age_limit=2):
        age = -1
        h = self.history.get(address, [])
        if h == ['*']:
            return True
        for tx_hash, tx_height in h:
            if tx_height == 0:
                tx_age = 0
            else:
                tx_age = self.network.get_local_height() - tx_height + 1
            if tx_age > age:
                age = tx_age
        return age > age_limit

    def can_sign(self, tx):
        if self.is_watching_only():
            return False
        if tx.is_complete():
            return False
        for x in tx.inputs_to_sign():
            if self.can_sign_xpubkey(x):
                return True
        return False


    def get_private_key_from_xpubkey(self, x_pubkey, password):
        if x_pubkey[0:2] in ['02','03','04']:
            addr = bitcoin.public_key_to_bc_address(x_pubkey.decode('hex'), self.active_chain.p2pkh_version)
            if self.is_mine(addr):
                return self.get_private_key(addr, password)[0]
        elif x_pubkey[0:2] == 'ff':
            xpub, sequence = BIP32_Account.parse_xpubkey(x_pubkey)
            for k, account in self.accounts.items():
                if xpub in account.get_master_pubkeys():
                    pk = account.get_private_key(sequence, self, password)
                    return pk[0]
        elif x_pubkey[0:2] == 'fe':
            xpub, sequence = OldAccount.parse_xpubkey(x_pubkey)
            for k, account in self.accounts.items():
                if xpub in account.get_master_pubkeys():
                    pk = account.get_private_key(sequence, self, password)
                    return pk[0]
        elif x_pubkey[0:2] == 'fd':
            addrtype = ord(x_pubkey[2:4].decode('hex'))
            addr = hash_160_to_bc_address(x_pubkey[4:].decode('hex'), addrtype)
            if self.is_mine(addr):
                return self.get_private_key(addr, password)[0]
        else:
            raise BaseException("z")


    def can_sign_xpubkey(self, x_pubkey):
        if x_pubkey[0:2] in ['02','03','04']:
            addr = bitcoin.public_key_to_bc_address(x_pubkey.decode('hex'), self.active_chain.p2pkh_version)
            return self.is_mine(addr)
        elif x_pubkey[0:2] == 'ff':
            xpub, sequence = BIP32_Account.parse_xpubkey(x_pubkey)
            return xpub in [ self.master_public_keys[k] for k in self.master_private_keys.keys() ]
        elif x_pubkey[0:2] == 'fe':
            xpub, sequence = OldAccount.parse_xpubkey(x_pubkey)
            return xpub == self.get_master_public_key()
        elif x_pubkey[0:2] == 'fd':
            addrtype = ord(x_pubkey[2:4].decode('hex'))
            addr = hash_160_to_bc_address(x_pubkey[4:].decode('hex'), addrtype)
            return self.is_mine(addr)
        else:
            raise BaseException("z")


    def is_watching_only(self):
        False

    def can_change_password(self):
        return not self.is_watching_only()

    def get_all_labels(self):
        chaincodes = chainparams.known_chain_codes
        labels = {}
        for code in sorted(chaincodes):
            d = self.storage.get_chain_value(code, 'labels', {})
            labels[code] = d
        return labels

    def set_all_labels(self, new_labels):
        chaincodes = chainparams.known_chain_codes
        for code, d in new_labels.items():
            if not chainparams.is_known_chain(code):
                continue
            # is_known_chain does code.upper(), so we need to do this
            # as well to make sure it's really upper case
            self.storage.set_chain_value(code.upper(), 'labels', d)

class Imported_Wallet(Abstract_Wallet):
    wallet_type = 'imported'

    def __init__(self, storage):
        Abstract_Wallet.__init__(self, storage)
        a = self.accounts.get(IMPORTED_ACCOUNT)
        if not a:
            self.accounts[IMPORTED_ACCOUNT] = ImportedAccount({'imported':{}})

    def is_watching_only(self):
        acc = self.accounts[IMPORTED_ACCOUNT]
        n = acc.keypairs.values()
        return n == [[None, None]] * len(n)

    def has_seed(self):
        return False

    def is_deterministic(self):
        return False

    def check_password(self, password):
        self.accounts[IMPORTED_ACCOUNT].get_private_key((0,0), self, password)

    def is_used(self, address):
        h = self.history.get(address,[])
        return len(h), False

    def get_master_public_keys(self):
        return {}

    def is_beyond_limit(self, address, account, is_change):
        return False


class Deterministic_Wallet(Abstract_Wallet):

    def __init__(self, storage):
        Abstract_Wallet.__init__(self, storage)

    def has_seed(self):
        return self.seed != ''

    def is_deterministic(self):
        return True

    def is_watching_only(self):
        return not self.has_seed()

    def add_seed(self, seed, password):
        if self.seed:
            raise Exception("a seed exists")

        self.seed_version, self.seed = self.format_seed(seed)
        if password:
            self.seed = pw_encode( self.seed, password)
            self.use_encryption = True
        else:
            self.use_encryption = False

        self.storage.put_above_chain('seed', self.seed, True)
        self.storage.put_above_chain('seed_version', self.seed_version, True)
        self.storage.put_above_chain('use_encryption', self.use_encryption,True)

    def get_seed(self, password):
        return pw_decode(self.seed, password)

    def get_mnemonic(self, password):
        return self.get_seed(password)

    def change_gap_limit(self, value):
        if value >= self.gap_limit:
            self.gap_limit = value
            self.storage.put('gap_limit', self.gap_limit, True)
            #self.interface.poke('synchronizer')
            return True

        elif value >= self.min_acceptable_gap():
            for key, account in self.accounts.items():
                addresses = account[0]
                k = self.num_unused_trailing_addresses(addresses)
                n = len(addresses) - k + value
                addresses = addresses[0:n]
                self.accounts[key][0] = addresses

            self.gap_limit = value
            self.storage.put('gap_limit', self.gap_limit, True)
            self.save_accounts()
            return True
        else:
            return False

    def num_unused_trailing_addresses(self, addresses):
        k = 0
        for a in addresses[::-1]:
            if self.history.get(a):break
            k = k + 1
        return k

    def min_acceptable_gap(self):
        # fixme: this assumes wallet is synchronized
        n = 0
        nmax = 0

        for account in self.accounts.values():
            addresses = account.get_addresses(0)
            k = self.num_unused_trailing_addresses(addresses)
            for a in addresses[0:-k]:
                if self.history.get(a):
                    n = 0
                else:
                    n += 1
                    if n > nmax: nmax = n
        return nmax + 1

    def default_account(self):
        return self.accounts['0']

    def create_new_address(self, account=None, for_change=0):
        if account is None:
            account = self.default_account()
        address = account.create_new_address(for_change)
        self.add_address(address)
        return address

    def add_address(self, address):
        if address not in self.history:
            self.history[address] = []
        if self.synchronizer:
            self.synchronizer.add(address)
        self.save_accounts()

    def synchronize(self):
        for account in self.accounts.values():
            account.synchronize(self)

    def restore(self, callback):
        from i18n import _
        def wait_for_wallet():
            self.set_up_to_date(False)
            while not self.is_up_to_date():
                msg = "%s\n%s %d"%(
                    _("Please wait..."),
                    _("Addresses generated:"),
                    len(self.addresses(True)))

                apply(callback, (msg,))
                time.sleep(0.1)

        def wait_for_network():
            while not self.network.is_connected():
                msg = "%s \n" % (_("Connecting..."))
                apply(callback, (msg,))
                time.sleep(0.1)

        # wait until we are connected, because the user might have selected another server
        if self.network:
            wait_for_network()
            wait_for_wallet()
        else:
            self.synchronize()
        self.fill_addressbook()


    def is_beyond_limit(self, address, account, is_change):
        if type(account) == ImportedAccount:
            return False
        addr_list = account.get_addresses(is_change)
        i = addr_list.index(address)
        prev_addresses = addr_list[:max(0, i)]
        limit = self.gap_limit_for_change if is_change else self.gap_limit
        if len(prev_addresses) < limit:
            return False
        prev_addresses = prev_addresses[max(0, i - limit):]
        for addr in prev_addresses:
            if self.history.get(addr):
                return False
        return True

    def get_action(self):
        if not self.get_master_public_key():
            return 'create_seed'
        if not self.accounts:
            return 'create_accounts'

    def get_master_public_keys(self):
        out = {}
        for k, account in self.accounts.items():
            name = self.get_account_name(k)
            mpk_text = '\n\n'.join( account.get_master_pubkeys() )
            out[name] = mpk_text
        return out



class BIP32_Wallet(Deterministic_Wallet):
    # abstract class, bip32 logic
    gap_limit = 20

    def __init__(self, storage):
        Deterministic_Wallet.__init__(self, storage)
        self.master_public_keys  = storage.get('master_public_keys', {})
        self.master_private_keys = storage.get('master_private_keys', {})

    def is_watching_only(self):
        return not bool(self.master_private_keys)

    def get_master_public_key(self):
        return self.master_public_keys.get(self.root_name)

    def get_master_private_key(self, account, password):
        k = self.master_private_keys.get(account)
        if not k: return
        xprv = pw_decode(k, password)
        return xprv

    def check_password(self, password):
        xpriv = self.get_master_private_key(self.root_name, password)
        xpub = self.master_public_keys[self.root_name]
        assert deserialize_xkey(xpriv)[3] == deserialize_xkey(xpub)[3]

    def add_master_public_key(self, name, xpub):
        self.master_public_keys[name] = xpub
        self.storage.put('master_public_keys', self.master_public_keys, True)

    def add_master_private_key(self, name, xpriv, password):
        self.master_private_keys[name] = pw_encode(xpriv, password)
        self.storage.put('master_private_keys', self.master_private_keys, True)

    def derive_xkeys(self, root, derivation, password):
        x = self.master_private_keys[root]
        root_xprv = pw_decode(x, password)
        xprv, xpub = bip32_private_derivation(root_xprv, root, derivation)
        return xpub, xprv

    def create_master_keys(self, password):
        seed = self.get_seed(password)
        self.add_cosigner_seed(seed, self.root_name, password)

    def add_cosigner_seed(self, seed, name, password):
        # we don't store the seed, only the master xpriv
        xprv, xpub = bip32_root(self.mnemonic_to_seed(seed,''))
        xprv, xpub = bip32_private_derivation(xprv, "m/", self.root_derivation)
        self.add_master_public_key(name, xpub)
        self.add_master_private_key(name, xprv, password)

    def add_cosigner_xpub(self, seed, name):
        # store only master xpub
        xprv, xpub = bip32_root(self.mnemonic_to_seed(seed,''))
        xprv, xpub = bip32_private_derivation(xprv, "m/", self.root_derivation)
        self.add_master_public_key(name, xpub)

    def mnemonic_to_seed(self, seed, password):
         return Mnemonic.mnemonic_to_seed(seed, password)

    def make_seed(self):
        lang = self.storage.config.get_above_chain('language')
        return Mnemonic(lang).make_seed()

    def format_seed(self, seed):
        return NEW_SEED_VERSION, ' '.join(seed.split())


class BIP32_Simple_Wallet(BIP32_Wallet):
    # Wallet with a single BIP32 account, no seed
    # gap limit 20
    root_name = 'x/'
    wallet_type = 'xpub'

    def create_xprv_wallet(self, xprv, password):
        xpub = bitcoin.xpub_from_xprv(xprv)
        account = BIP32_Account({'xpub':xpub})
        self.storage.put('seed_version', self.seed_version, True)
        self.add_master_private_key(self.root_name, xprv, password)
        self.add_master_public_key(self.root_name, xpub)
        self.add_account('0', account)

    def create_xpub_wallet(self, xpub):
        account = BIP32_Account({'xpub':xpub})
        self.storage.put('seed_version', self.seed_version, True)
        self.add_master_public_key(self.root_name, xpub)
        self.add_account('0', account)


class BIP32_HD_Wallet(BIP32_Wallet):
    # wallet that can create accounts
    def __init__(self, storage):
        self.next_account = storage.get('next_account', None)
        BIP32_Wallet.__init__(self, storage)

    def can_create_accounts(self):
        return self.root_name in self.master_private_keys.keys()

    def addresses(self, b=True):
        l = BIP32_Wallet.addresses(self, b)
#        if self.next_account:
#            _, _, next_address = self.next_account
#            if next_address not in l:
#                l.append(next_address)
        return l

    def get_address_index(self, address):
        if self.next_account:
            next_id, next_xpub, next_address = self.next_account
            if address == next_address:
                return next_id, (0,0)
        return BIP32_Wallet.get_address_index(self, address)

    def num_accounts(self):
        keys = []
        for k, v in self.accounts.items():
            if type(v) != BIP32_Account:
                continue
            keys.append(k)
        i = 0
        while True:
            account_id = '%d'%i
            if account_id not in keys:
                break
            i += 1
        return i

    def get_next_account(self, password):
        account_id = '%d'%self.num_accounts()
        derivation = self.root_name + "%d'"%int(account_id)
        xpub, xprv = self.derive_xkeys(self.root_name, derivation, password)
        self.add_master_public_key(derivation, xpub)
        if xprv:
            self.add_master_private_key(derivation, xprv, password)
        account = BIP32_Account({'xpub':xpub})
        addr = account.first_address()
        self.add_address(addr)
        return account_id, xpub, addr

    def create_main_account(self, password):
        # First check the password is valid (this raises if it isn't).
        self.check_password(password)
        assert self.num_accounts() == 0
        self.create_account('Main account', password)

    def create_account(self, name, password):
        account_id, xpub, addr = self.get_next_account(password)
        account = BIP32_Account({'xpub':xpub})
        self.add_account(account_id, account)
        self.set_label(account_id, name)
        # add address of the next account
        self.next_account = self.get_next_account(password)
        self.storage.put('next_account', self.next_account)

    def account_is_pending(self, k):
        return type(self.accounts.get(k)) == PendingAccount

    def delete_pending_account(self, k):
        assert type(self.accounts.get(k)) == PendingAccount
        self.accounts.pop(k)
        self.save_accounts()

    def create_pending_account(self, name, password):
        next_id, next_xpub, next_address = self.next_account if self.next_account else self.get_next_account(password)
        self.set_label(next_id, name)
        self.accounts[next_id] = PendingAccount({'pending':next_address})
        self.save_accounts()

    def synchronize(self):
        # synchronize existing accounts
        BIP32_Wallet.synchronize(self)

        if self.next_account is None:
            try:
                self.next_account = self.get_next_account(None)
                self.storage.put('next_account', self.next_account)
            except:
                pass

        # check pending account
        if self.next_account is not None:
            next_id, next_xpub, next_address = self.next_account
            if self.address_is_old(next_address):
                print_error("creating account", next_id)
                self.add_account(next_id, BIP32_Account({'xpub':next_xpub}))
                # here the user should get a notification
                self.next_account = None
                self.storage.put('next_account', self.next_account)
            elif self.history.get(next_address, []):
                if next_id not in self.accounts:
                    print_error("create pending account", next_id)
                    self.accounts[next_id] = PendingAccount({'pending':next_address})
                    self.save_accounts()



class NewWallet(BIP32_HD_Wallet, Mnemonic):
    # bip 44
    root_name = 'x/'
    root_derivation = "m/44'/0'"
    wallet_type = 'standard'

    def __init__(self, storage):
        BIP32_HD_Wallet.__init__(self, storage)
        chain_index = chainparams.get_chain_index(self.active_chain_code)
        self.root_derivation = "m/44'/{}'".format(chain_index)

    def get_action(self):
        if self.seed == '':
            return 'create_seed'
        if not self.get_master_public_key():
            return 'add_chain'
        if not self.accounts:
            return 'create_accounts'

# Multisig wallets use a different derivation path
# Instead of m/44'/coin'/... we use m/1491'/0'/coin/...
# Keys are derived in this manner:
# Cosigners share public keys. For a given chain, the public key used
# in the main account is the chain_index-th non-hardened child of
# the master public key.
#
# Example
# The public key that we share with our cosigner is m/1491'/0'
# To generate addresses for Bitcoin,  we use m/1491'/0'/0/for_change/index  as the key in the script hash.
# To generate addresses for Mazacoin, we use m/1491'/0'/13/for_change/index as the key in the script hash.
class Multisig_Wallet(BIP32_Wallet, Mnemonic):
    root_name = "x1/"
    root_derivation = "m/1491'/0'"

    def __init__(self, storage):
        BIP32_Wallet.__init__(self, storage)
        try:
            chain_code = storage.config.get_active_chain_code()
        # constructor was passed a dict instead of a config object
        except AttributeError:
            chain_code = chainparams.get_active_chain().code
        if chain_code is None:
            chain_code = chainparams.get_active_chain().code

        chain_index = chainparams.get_chain_index(chain_code)
        self.root_derivation = "m/1491'/0'"

        self.master_public_keys  = storage.get_above_chain('master_public_keys', {})
        self.master_private_keys = storage.get_above_chain('master_private_keys', {})

    def can_import(self):
        return False

    def add_master_public_key(self, name, xpub):
        self.master_public_keys[name] = xpub
        self.storage.put_above_chain('master_public_keys', self.master_public_keys, True)

    def add_master_private_key(self, name, xpriv, password):
        self.master_private_keys[name] = pw_encode(xpriv, password)
        self.storage.put_above_chain('master_private_keys', self.master_private_keys, True)

    def can_sign_xpubkey(self, x_pubkey):
        if x_pubkey[0:2] in ['02','03','04']:
            addr = bitcoin.public_key_to_bc_address(x_pubkey.decode('hex'), self.active_chain.p2pkh_version)
            return self.is_mine(addr)
        elif x_pubkey[0:2] == 'ff':
            xpub, sequence = BIP32_Account.parse_xpubkey(x_pubkey)
            for k, account in self.accounts.items():
                if xpub == account.get_master_pubkeys()[0]:
                    return True
            return False
        elif x_pubkey[0:2] == 'fe':
            xpub, sequence = OldAccount.parse_xpubkey(x_pubkey)
            return xpub == self.get_master_public_key()
        elif x_pubkey[0:2] == 'fd':
            addrtype = ord(x_pubkey[2:4].decode('hex'))
            addr = hash_160_to_bc_address(x_pubkey[4:].decode('hex'), addrtype)
            return self.is_mine(addr)
        else:
            raise BaseException("z")

    def get_private_key_from_xpubkey(self, x_pubkey, password):
        if x_pubkey[0:2] in ['02','03','04']:
            addr = bitcoin.public_key_to_bc_address(x_pubkey.decode('hex'), self.active_chain.p2pkh_version)
            if self.is_mine(addr):
                return self.get_private_key(addr, password)[0]
        elif x_pubkey[0:2] == 'ff':
            xpub, sequence = BIP32_Account.parse_xpubkey(x_pubkey)
            for k, account in self.accounts.items():
                if xpub == account.get_master_pubkeys()[0]:
                    pk = account.get_private_key(sequence, self, password)
                    return pk[0]
        elif x_pubkey[0:2] == 'fe':
            xpub, sequence = OldAccount.parse_xpubkey(x_pubkey)
            for k, account in self.accounts.items():
                if xpub in account.get_master_pubkeys():
                    pk = account.get_private_key(sequence, self, password)
                    return pk[0]
        elif x_pubkey[0:2] == 'fd':
            addrtype = ord(x_pubkey[2:4].decode('hex'))
            addr = hash_160_to_bc_address(x_pubkey[4:].decode('hex'), addrtype)
            if self.is_mine(addr):
                return self.get_private_key(addr, password)[0]
        else:
            raise BaseException("z")

    def sign_transaction(self, tx, password):
        if self.is_watching_only():
            return
        # check that the password is correct. This will raise if it's not.
        self.check_password(password)
        keypairs = {}
        x_pubkeys = tx.inputs_to_sign()
        for x in x_pubkeys:
            sec = self.get_private_key_from_xpubkey(x, password)
            print "sec", sec
            if sec:
                keypairs[ x ] = sec
        if keypairs:
            tx.sign(keypairs)
        run_hook('sign_transaction', tx, password)

class Wallet_2of2(Multisig_Wallet):
    # Wallet with multisig addresses.
    # Cannot create accounts
    wallet_type = '2of2'

    def __init__(self, storage):
        Multisig_Wallet.__init__(self, storage)

    def can_import(self):
        return False

    def create_main_account(self, password):
        xpub1 = self.master_public_keys.get("x1/")
        xpub2 = self.master_public_keys.get("x2/")
        acc_xpub1 = bip32_public_derivation(xpub1, "", "/{}".format(self.active_chain.chain_index))
        acc_xpub2 = bip32_public_derivation(xpub2, "", "/{}".format(self.active_chain.chain_index))
        account = BIP32_Account_2of2({'xpub':acc_xpub1, 'xpub2':acc_xpub2})
        self.add_account('0', account)

    def get_master_public_keys(self):
        xpub1 = self.master_public_keys.get("x1/")
        xpub2 = self.master_public_keys.get("x2/")
        return {'x1':xpub1, 'x2':xpub2}

    def get_action(self):
        xpub1 = self.master_public_keys.get("x1/")
        xpub2 = self.master_public_keys.get("x2/")
        if xpub1 is None:
            return 'create_seed'
        if xpub2 is None:
            return 'add_cosigner'
        if not self.accounts:
            return 'create_accounts'



class Wallet_2of3(Wallet_2of2):
    # multisig 2 of 3
    wallet_type = '2of3'

    def create_main_account(self, password):
        xpub1 = self.master_public_keys.get("x1/")
        xpub2 = self.master_public_keys.get("x2/")
        xpub3 = self.master_public_keys.get("x3/")
        acc_xpub1 = bip32_public_derivation(xpub1, "", "/{}".format(self.active_chain.chain_index))
        acc_xpub2 = bip32_public_derivation(xpub2, "", "/{}".format(self.active_chain.chain_index))
        acc_xpub3 = bip32_public_derivation(xpub3, "", "/{}".format(self.active_chain.chain_index))
        account = BIP32_Account_2of3({'xpub':acc_xpub1, 'xpub2':acc_xpub2, 'xpub3':acc_xpub3})
        self.add_account('0', account)

    def get_master_public_keys(self):
        xpub1 = self.master_public_keys.get("x1/")
        xpub2 = self.master_public_keys.get("x2/")
        xpub3 = self.master_public_keys.get("x3/")
        return {'x1':xpub1, 'x2':xpub2, 'x3':xpub3}

    def get_action(self):
        xpub1 = self.master_public_keys.get("x1/")
        xpub2 = self.master_public_keys.get("x2/")
        xpub3 = self.master_public_keys.get("x3/")
        if xpub1 is None:
            return 'create_seed'
        if xpub2 is None or xpub3 is None:
            return 'add_two_cosigners'
        if not self.accounts:
            return 'create_accounts'

class Wallet_MofN(Multisig_Wallet):
    wallet_type = 'mofn'

    def __init__(self, storage):
        Multisig_Wallet.__init__(self, storage)
        self.multisig_m = storage.get_above_chain('multisig_m')
        self.multisig_n = storage.get_above_chain('multisig_n')

    def create_main_account(self, password):
        xpubs = self.master_public_keys.items()
        acc_dict = {}
        acc_xpubs = {}
        for k, v in xpubs:
            if k == "x1/":
                acc_dict[ 'xpub' ] = bip32_public_derivation(v, "", "/{}".format(self.active_chain.chain_index))
            else:
                acc_xpubs[ "xpub{}".format(k[1]) ] = bip32_public_derivation(v, "", "/{}".format(self.active_chain.chain_index))
        acc_dict['cosigner_xpubs'] = acc_xpubs
        acc_dict['multisig_m'] = self.multisig_m
        acc_dict['multisig_n'] = self.multisig_n
        # acc_dict: {
        # 'xpub': MY_XPUB,
        # 'cosigner_xpubs': {
        #   'xpub2': XPUB_NUMBER_2,
        #   'xpub3': XPUB_NUMBER_3
        #  }
        # }
        account = BIP32_Account_MofN(acc_dict)
        self.add_account('0', account)

    def get_master_public_keys(self):
        d = {}
        for k, v in self.master_public_keys.items():
            d[ k[:-1] ] = v
        return d

    def set_m_and_n(self, m, n):
        if not is_standard_mofn(m, n):
            return
        self.multisig_m = m
        self.multisig_n = n
        self.storage.put_above_chain('multisig_m', self.multisig_m)
        self.storage.put_above_chain('multisig_n', self.multisig_n)

    def get_action(self):
        xpubs = self.master_public_keys
        if not self.multisig_m or not self.multisig_n:
            return 'add_m_and_n'
        missing_xpubs = self.multisig_n - len(xpubs.keys())
        if xpubs.get("x1/") is None:
            return 'create_seed'
        if missing_xpubs > 0:
            return 'add_x_cosigners:{}'.format(missing_xpubs)
        if not self.accounts:
            return 'create_accounts'

class OldWallet(Deterministic_Wallet):
    wallet_type = 'old'
    gap_limit = 5

    def __init__(self, storage):
        Deterministic_Wallet.__init__(self, storage)
        self.gap_limit = storage.get('gap_limit', 5)

    def make_seed(self):
        import old_mnemonic
        seed = random_seed(128)
        return ' '.join(old_mnemonic.mn_encode(seed))

    def format_seed(self, seed):
        import old_mnemonic
        # see if seed was entered as hex
        seed = seed.strip()
        try:
            assert seed
            seed.decode('hex')
            return OLD_SEED_VERSION, str(seed)
        except Exception:
            pass

        words = seed.split()
        seed = old_mnemonic.mn_decode(words)
        if not seed:
            raise Exception("Invalid seed")

        return OLD_SEED_VERSION, seed

    def create_master_keys(self, password):
        seed = self.get_seed(password)
        mpk = OldAccount.mpk_from_seed(seed)
        self.storage.put('master_public_key', mpk, True)

    def get_master_public_key(self):
        return self.storage.get("master_public_key")

    def get_master_public_keys(self):
        return {'Main Account':self.get_master_public_key()}

    def create_main_account(self, password):
        mpk = self.storage.get("master_public_key")
        self.create_account(mpk)

    def create_account(self, mpk):
        self.accounts['0'] = OldAccount({'mpk':mpk, 0:[], 1:[]})
        self.save_accounts()

    def create_watching_only_wallet(self, mpk):
        self.seed_version = OLD_SEED_VERSION
        self.storage.put('seed_version', self.seed_version, True)
        self.storage.put('master_public_key', mpk, True)
        self.create_account(mpk)

    def get_seed(self, password):
        seed = pw_decode(self.seed, password).encode('utf8')
        return seed

    def check_password(self, password):
        seed = self.get_seed(password)
        self.accounts['0'].check_seed(seed)

    def get_mnemonic(self, password):
        import old_mnemonic
        s = self.get_seed(password)
        return ' '.join(old_mnemonic.mn_encode(s))




wallet_types = [
    # category   type        description                   constructor
    ('standard', 'old',      ("Old wallet"),               OldWallet),
    ('standard', 'xpub',     ("BIP32 Import"),             BIP32_Simple_Wallet),
    ('standard', 'standard', ("Standard wallet"),          NewWallet),
    ('standard', 'imported', ("Imported wallet"),          Imported_Wallet),
    ('multisig', '2of2',     ("Multisig wallet (2 of 2)"), Wallet_2of2),
    ('multisig', '2of3',     ("Multisig wallet (2 of 3)"), Wallet_2of3),
    ('multisig', 'mofn',     ("Multisig wallet (M of N)"), Wallet_MofN)
]

# former WalletFactory
class Wallet(object):
    """The main wallet "entry point".
    This class is actually a factory that will return a wallet of the correct
    type when passed a WalletStorage instance."""

    def __new__(self, storage):

        seed_version = storage.get('seed_version')
        if not seed_version:
            seed_version = OLD_SEED_VERSION if len(storage.get('master_public_key','')) == 128 else NEW_SEED_VERSION

        if seed_version not in [OLD_SEED_VERSION, NEW_SEED_VERSION]:
            msg = "This wallet seed is not supported anymore."
            if seed_version in [5, 7, 8, 9]:
                msg += "\nTo open this wallet, try 'git checkout seed_v%d'"%seed_version
            print msg
            sys.exit(1)

        run_hook('add_wallet_types', wallet_types)
        wallet_type = storage.get_above_chain('wallet_type')
        # If wallet_type isn't above chain, get it from where it used to be
        if wallet_type is None:
            wallet_type = storage.get('wallet_type')
        if wallet_type:
            for cat, t, name, c in wallet_types:
                if t == wallet_type:
                    WalletClass = c
                    break
            else:
                raise BaseException('unknown wallet type', wallet_type)
        else:
            if seed_version == OLD_SEED_VERSION:
                WalletClass = OldWallet
            else:
                WalletClass = NewWallet

        return WalletClass(storage)

    @classmethod
    def is_seed(self, seed):
        if not seed:
            return False
        elif is_old_seed(seed):
            return True
        elif is_new_seed(seed):
            return True
        else:
            return False

    @classmethod
    def is_old_mpk(self, mpk):
        try:
            int(mpk, 16)
            assert len(mpk) == 128
            return True
        except:
            return False

    @classmethod
    def is_xpub(self, text):
        try:
            assert text[0:4] == 'xpub'
            deserialize_xkey(text)
            return True
        except:
            return False

    @classmethod
    def is_xprv(self, text):
        try:
            assert text[0:4] == 'xprv'
            deserialize_xkey(text)
            return True
        except:
            return False

    @classmethod
    def is_address(self, text):
        if not text:
            return False
        for x in text.split():
            if not base58.is_address(x):
                return False
        return True

    @classmethod
    def is_private_key(self, text):
        if not text:
            return False
        for x in text.split():
            if not base58.is_private_key(x, chainparams.get_active_chain().wif_version):
                return False
        return True

    @classmethod
    def from_seed(self, seed, storage):
        if is_old_seed(seed):
            klass = OldWallet
        elif is_new_seed(seed):
            klass = NewWallet
        w = klass(storage)
        return w

    @classmethod
    def from_address(self, text, storage):
        w = Imported_Wallet(storage)
        for x in text.split():
            w.accounts[IMPORTED_ACCOUNT].add(x, None, None, None)
        w.save_accounts()
        return w

    @classmethod
    def from_private_key(self, text, storage):
        w = Imported_Wallet(storage)
        for x in text.split():
            w.import_key(x, None)
        return w

    @classmethod
    def from_old_mpk(self, mpk, storage):
        w = OldWallet(storage)
        w.seed = ''
        w.create_watching_only_wallet(mpk)
        return w

    @classmethod
    def from_xpub(self, xpub, storage):
        w = BIP32_Simple_Wallet(storage)
        w.create_xpub_wallet(xpub)
        return w

    @classmethod
    def from_xprv(self, xprv, password, storage):
        w = BIP32_Simple_Wallet(storage)
        w.create_xprv_wallet(xprv, password)
        return w

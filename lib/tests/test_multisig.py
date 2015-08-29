import shutil
import tempfile
import sys
import unittest

from StringIO import StringIO
from lib.bitcoin import bip32_root, bip32_private_derivation, bip32_public_derivation, xpub_from_xprv, deserialize_xkey
from lib.util_coin import int_to_hex
from lib.base58 import DecodeBase58Check, hash_160, hash_160_to_bc_address
from lib.account import BIP32_Account
from lib.wallet import WalletStorage, Wallet_2of2, Wallet_MofN
from lib import chainparams
from lib.transaction import Transaction
from lib.script import multisig_script


class FakeConfig(object):
    """A stub config file to be used in tests"""
    def __init__(self, path):
        self.path = path
        self.store = {'electrum_path': self.path}

    def __getitem__(self, key):
        return self.store[key]

    def keys(self):
        return self.store.keys()

    def set_active_chain_code(self, value, save=True):
        value = value.upper()
        if not chainparams.is_known_chain(value):
            return False
        self.store['active_chain_code'] = value
        if self.store.get(value,None) is None:
            self.store[value] = {}
        chainparams.set_active_chain(value)
        return True

    def get_active_chain_code(self, default=None):
        return self.store.get('active_chain_code', default)

    def get_above_chain(self, key, default=None):
        return self.store.get(key, default)

    def set_key_above_chain(self, key, value, save=True):
        self.store[key] = value

    def get_chain_config(self, chaincode):
        return self.get_above_chain(chaincode)

    def set_chain_config(self, chaincode, value):
        if not chainparams.is_known_chain(chaincode):
            return False
        return self.set_key_above_chain(chaincode, value)

    def set(self, key, value, save=True):
        chain_code = self.get_active_chain_code()
        try:
            self.store[chain_code][key] = value
        except AttributeError:
            self.store[chain_code] = {}
            self.store[chain_code][key] = value

    def set_key(self, key, value, save=True):
        return self.set(key, value, save)


    def get(self, key, default=None):
        return self.store.get(key, default)



class FakeSynchronizer(object):

    def __init__(self):
        self.store = []

    def add(self, address):
        self.store.append(address)


class WalletTestCase(unittest.TestCase):

    def setUp(self):
        super(WalletTestCase, self).setUp()
        self.user_dir = tempfile.mkdtemp()

        self.fake_config = FakeConfig(self.user_dir)
        self.fake_config.set_active_chain_code('BTC')

        self._saved_stdout = sys.stdout
        self._stdout_buffer = StringIO()
        sys.stdout = self._stdout_buffer

    def tearDown(self):
        super(WalletTestCase, self).tearDown()
        shutil.rmtree(self.user_dir)
        # Restore the "real" stdout
        sys.stdout = self._saved_stdout

class TestMultisigMofN(WalletTestCase):
    seed_text = "travel nowhere air position hill peace suffer parent beautiful rise blood power home crumble teach"
    password = "secret"

    # root keys (depth = 0)
    actual_root_privkey = 'xprv9s21ZrQH143K3cU1yF5gBUQqHw8QBnH5Cgym3XqSRZmfSJ3J2NYzjd7UcdHwjwBjKXD3ZvwoMLo88F4oaVhYgZZ5SdmZ9RA9Wdf93U8iZB3'
    cosigner1_root_privkey = 'xprv9s21ZrQH143K3Y15qhUgZ8wmLudbEGqxk7mcxzsAa4rEhEBZGi1dtC8CQoh3yo1pv2TaV6T7LJZQ8DyxUSwbYLJRrXSNoQQ7nrhetik8jaZ'
    cosigner2_root_privkey = 'xprv9s21ZrQH143K4PpqGoYdMXa5eCS1drqW7Zaw7he7Pq15mi3sqvqW5KE8rAd7MjZgXRCCADhg43Xyp7Ef52Gwf3goNXefuEbs31tsXoL2pM6'
    cosigner3_root_privkey = 'xprv9s21ZrQH143K3YEsjUQmm3pLJmu77SsRKchraCXcmNE2oqFQHJEgTCcN8qvNNn4n6iG1ZXYASG9XsK8JRtZhbBk9PVrmTZveU4AcSGauTvR'

    cosigner1_master_pubkey = None
    cosigner2_master_pubkey = None
    cosigner3_master_pubkey = None

    def setUp(self):
        super(TestMultisigMofN, self).setUp()
        self.storage = WalletStorage(self.fake_config)
        self.storage.put_above_chain('multisig_m', 3)
        self.storage.put_above_chain('multisig_n', 4)
        self.wallet = Wallet_MofN(self.storage)

        # set cosigner master privkey
        cosigner1_master_privkey = bip32_private_derivation(self.cosigner1_root_privkey, "m/", "m/1491'/0'")[0]
        self.cosigner1_master_pubkey = xpub_from_xprv(cosigner1_master_privkey)

        cosigner2_master_privkey = bip32_private_derivation(self.cosigner2_root_privkey, "m/", "m/1491'/0'")[0]
        self.cosigner2_master_pubkey = xpub_from_xprv(cosigner2_master_privkey)

        cosigner3_master_privkey = bip32_private_derivation(self.cosigner3_root_privkey, "m/", "m/1491'/0'")[0]
        self.cosigner3_master_pubkey = xpub_from_xprv(cosigner3_master_privkey)


        self.wallet.set_chain("BTC")
        self.wallet.add_seed(self.seed_text, self.password)
        self.wallet.create_master_keys(self.password)
        self.wallet.add_master_public_key("x2/", self.cosigner1_master_pubkey)
        self.wallet.add_master_public_key("x3/", self.cosigner2_master_pubkey)
        self.wallet.add_master_public_key("x4/", self.cosigner3_master_pubkey)
        self.wallet.create_main_account(self.password)

    def _switch_chain(self, chaincode):
        self.wallet.set_chain(chaincode)
        action = self.wallet.get_action()
        while action is not None:
            if action == 'add_chain':
                self.wallet.create_master_keys(self.password)
            elif action == 'create_accounts':
                self.wallet.create_main_account(self.password)
            action = self.wallet.get_action()

    def test_master_pubkey_derivation(self):
        self.assertEqual('xpub6B48x5PF7WJ73D9TvyEWFJpPgXxp1qVS8RVGttATwxvAmsfShE7sCGTME3D5SDDQAQtVwDQFLSAXYqxHtFix1LufTs3uEJwTRxfL9wJNp3s',
            self.wallet.master_public_keys.get("x1/"))
        self.assertEqual('xpub6ASQmDxzepDJ5i7fQgURxGfgFDEcWPNrjkEqFWYhkUEjAmKpBgj1Kbtt1tSRfYBBU11SJLDhU5HSjZSKNeY3o7t85ESDJAgFcPsEfVCBrSF',
            self.wallet.master_public_keys.get("x2/"))
        self.assertEqual('xpub6AQJU728LNY7LTxym8J1NDeaFzxsbZ3sLnwmteqRdhuzWWajkndMycDvQKGqmpdLNuYfDbs2x9FwHjVsVptHk7Ecdu9NSbbzFkQPogCStVM',
            self.wallet.master_public_keys.get("x3/"))
        self.assertEqual('xpub6AG4Qa384vkLrL9kcXZvbYRPbJAYBwmoidwErALZRkrQ796tiktqzUr9cQs69Kuj8ypuVs5mJtrb7SEokCokSZZKvsujpkD982W5RBbhRnC',
            self.wallet.master_public_keys.get("x4/"))

    def test_account(self):
        acc = self.wallet.accounts["0"]
        pubkeys = acc.get_master_pubkeys()
        self.assertIn('xpub6CfssEAJDCoTHU922RJy8oyXkdPNP8sMFxorzG9ncAbZjZRKCq5NFdRVybzvqHSPntpRDfHtGErXPbk1Y9uAJGJLZFtscVCMZP7mnRFqyQX', pubkeys)
        self.assertIn('xpub6Ckpjg1oUbAUwXAChU3eWAovMZTWmdMLFskZvRbVTbd8QNM5XG1WdBDubzFAkJjMMktsRRyyzhNKPuYaGNgroYuaz8R3fCGiLWBvmbXX1F2', pubkeys)
        self.assertIn('xpub6CWwK7DCdsCdi73o2KBwktuAWtXjzjMfDKcwgt9tYDZA8Es6SiXPbvaex96ZXhrQ1gxNRDfQFKkEBqeoLtB2biPypYRykpxmjbhYqXm7tEK', pubkeys)
        self.assertIn('xpub6DVpttCNu8vwewtVNMHFptokPeXSWEYUabg3bPFSeFQAWNmRtGBjgfnAFKvAPEvF6r1ym2rEbKVWvYY9dRyR1ZWA45uRkW5EzZxQNFhn5Mj', pubkeys)

        self.assertEqual(3, acc.multisig_m)
        self.assertEqual(4, acc.multisig_n)

    def test_redeem_script(self):
        acc = self.wallet.accounts["0"]

        x1_first_btc_key = bip32_public_derivation(self.wallet.master_public_keys.get("x1/"), "", "/0/0/0")
        x2_first_btc_key = bip32_public_derivation(self.wallet.master_public_keys.get("x2/"), "", "/0/0/0")
        x3_first_btc_key = bip32_public_derivation(self.wallet.master_public_keys.get("x3/"), "", "/0/0/0")
        x4_first_btc_key = bip32_public_derivation(self.wallet.master_public_keys.get("x4/"), "", "/0/0/0")
        x_pubkeys = [x1_first_btc_key, x2_first_btc_key, x3_first_btc_key, x4_first_btc_key]
        raw_pubkeys = map( lambda x: deserialize_xkey(x)[4], x_pubkeys )
        pubkeys = map( lambda x: x.encode('hex'), raw_pubkeys )

        # Compare redeem script to manually calculated one
        redeem_script = multisig_script(sorted(pubkeys), acc.multisig_m)
        self.assertEqual('53210278a1a7de63493a8c8e0e7f4ebb13fd2a8144db25bb3bc2e5f44127a851a389332102ee780aa224c9fe54caff984205077b7cca08ced3188a3f3c639d83deda6b9a592103124429ddbed55593d0abea0d0d3d283eca4546e40017b2945f4666c561b494ba210312872f0aa80fa1a9bc7df77fa5be310f5441f7bfec798fe19209b04954dec8da54ae', redeem_script)
        p2sh_addr = hash_160_to_bc_address( hash_160(redeem_script.decode('hex')), self.wallet.active_chain.p2sh_version )
        self.assertEqual("32Ktuh5jGEAAJyNXQE7f1LUAcMXSfvdSzE", p2sh_addr)

    def test_transaction(self):

        wallet_keys = {
            'xpub6GDQf5vZmrpQvD4ixNdqHmgSZ76Uo2Cg5isBupnvZpnNbhdRhgdhq9hkfCSKRE31rGfYuXNfZ5gTamFkj1GXt6k87MD1hUn28tuvLHY71Bk': 'L2FQCaHPwgS4CmAf6bKtbjVWDbcHv42c72by1zLEyLuDrUG22CwM',
            'xpub6GLs33TeHkrLSTJ2uxiMLnuqxCHG9iBFCwjTwyg4EvzyxUi78U1sXxxRPUQfLGNEZRT3yYKEwR39ZbUtofEgcmTLtJdSetnFiQPEwTZRW5y': 'L1aD1WSA3UGU56sAmjfYVj1rK3fnSzWKj2wTsDTN1DpgUgPVwQCa',
            'xpub6Fc64k9RTc79yD7xErF2yKSdUraGBhGWDt1FomUFVCFg52165LZvvoGL59hebJBGtauFqNL5zMeRgPGV29sfQp6XqoiiD9E53UDatBhFZuk': 'L25eCRYrDNVNrTZV1XZhmaZti3dVsZz3egm1R7LsPHRdpYuyLYKE'
#            'xpub6GiSmJrVQC5q2m5cRcZvUgnGUsfeEqi3eEfUTgacnA33G8PAQnJeeMzpNAGUA9JL3goUui7BY52rVPwhmxMALkmFh5ZuwJDKrPv8ERkG3CK': 'L3jUPoR7fUwB9mwfuqqF79mHDpj5rpygQhdWntJ9ShZ9nbyRab5h'
        }

        acc = self.wallet.accounts["0"]
        redeem_script = '53210278a1a7de63493a8c8e0e7f4ebb13fd2a8144db25bb3bc2e5f44127a851a389332102ee780aa224c9fe54caff984205077b7cca08ced3188a3f3c639d83deda6b9a592103124429ddbed55593d0abea0d0d3d283eca4546e40017b2945f4666c561b494ba210312872f0aa80fa1a9bc7df77fa5be310f5441f7bfec798fe19209b04954dec8da54ae'

        coins = [ {'address': '32SbQbBthcMzRSpCw1ifAXqWviJGH5HKUk',
            'value': 600000,
            'prevout_n': 0,
            'prevout_hash': '1111111111111111111111111111111111111111111111111111111111111111',
            'height': 100000,
            'coinbase': 'True'
            } ]

        txin = coins[0]

        x_pubkeys = map( lambda x:bip32_public_derivation(x, "", "/0/0/0"), self.wallet.master_public_keys.values() )
        pubkeys = map(lambda x: deserialize_xkey(x)[4].encode('hex'), x_pubkeys)

        s = ''.join( map(lambda x: int_to_hex(x, 2), (0, 0)))
        x_pubkeys = map( lambda x: 'ff' + DecodeBase58Check(x).encode('hex') + s, x_pubkeys)
        pubkeys, x_pubkeys = zip( *sorted(zip(pubkeys, x_pubkeys)))
        txin['pubkeys'] = list(pubkeys)
        txin['x_pubkeys'] = list(x_pubkeys)
        txin['signatures'] = [None] * len(pubkeys)
        txin['redeemScript'] = redeem_script
        txin['num_sig'] = acc.multisig_m

        outputs = [ ('address', '1PyXgL1qmZPuxcVi9CcguQb3v7WUvQZBud', 500000) ]
        inputs = []
        tx = Transaction(inputs, outputs)
        tx.add_input(txin)
        self.wallet.sign_transaction(tx, "secret")

        #
        ins = tx.inputs_to_sign()
        keypairs = {}
        sec = None
        for innard in ins:
            # this is easier than the commented loop below
            in_xpub, _ = BIP32_Account.parse_xpubkey(innard)
            if wallet_keys.get(in_xpub):
                keypairs[ innard ] = wallet_keys[in_xpub]
            # ...
#            in_xpub, in_seq = BIP32_Account.parse_xpubkey(innard)
#            sec = None
#            for k, vaccount in self.wallet.accounts.items():
#                acc_v = vaccount.get_master_pubkeys()[0]
#                acc_xpub = bip32_public_derivation(acc_v, "", "/0/0")
#                if in_xpub == acc_xpub:
#                    pk = vaccount.get_private_key(in_seq, self.wallet, "secret")
#                    sec = pk[0]

#            if sec:
#                keypairs [ innard ] = sec

        if keypairs:
            tx.sign(keypairs)
        self.assertEqual('0100000001111111111111111111111111111111111111111111111111111111111111111100000000fd6701004730440220774e80fda89895d8bf3ac39c38f39456d31c1e857dc1c77c000f4de6c3de15fe02207b6d13b5ba17eadeb607f3ca56f693a0b777dae668584cefec0910a8bc90869a0147304402205e80562254972f873b5b59b1cdc81e422c7a2959d8868e5a54238fbfdf6f107002200204eef593812453ae2c22334c409f9ef25523cf9619399eb2d3c249673443dc01483045022100a81e69796aa5e5ae0d8924047e3c81a8dd64dfbc791caba6728ac7820aa114da022060b85875fd58223b7c61ef45fac2567a9f76934f947e4d03d927f5b078e1fb45014c8b53210278a1a7de63493a8c8e0e7f4ebb13fd2a8144db25bb3bc2e5f44127a851a389332102ee780aa224c9fe54caff984205077b7cca08ced3188a3f3c639d83deda6b9a592103124429ddbed55593d0abea0d0d3d283eca4546e40017b2945f4666c561b494ba210312872f0aa80fa1a9bc7df77fa5be310f5441f7bfec798fe19209b04954dec8da54aeffffffff0120a10700000000001976a914fc03ab7c28d17349f084f7cadde4dafc356918d388ac00000000', str(tx))

        ###########
        #
        serialized_tx = str(tx)
        tx2 = Transaction.deserialize(serialized_tx, active_chain = self.wallet.active_chain)
        self.assertEquals(4, len(  tx2.inputs[0]['x_pubkeys'])  )
        self.assertEquals(3, tx2.inputs[0]['num_sig']  )

class TestMultisigWallet(WalletTestCase):

    seed_text = "travel nowhere air position hill peace suffer parent beautiful rise blood power home crumble teach"
    password = "secret"

    # mnemonic_to_seed should be this
    actual_root_privkey = 'xprv9s21ZrQH143K3cU1yF5gBUQqHw8QBnH5Cgym3XqSRZmfSJ3J2NYzjd7UcdHwjwBjKXD3ZvwoMLo88F4oaVhYgZZ5SdmZ9RA9Wdf93U8iZB3'
    cosigner_root_privkey = 'xprv9s21ZrQH143K3Y15qhUgZ8wmLudbEGqxk7mcxzsAa4rEhEBZGi1dtC8CQoh3yo1pv2TaV6T7LJZQ8DyxUSwbYLJRrXSNoQQ7nrhetik8jaZ'

    cosigner_master_pubkey = None

    def setUp(self):
        super(TestMultisigWallet, self).setUp()
        self.storage = WalletStorage(self.fake_config)
        self.wallet = Wallet_2of2(self.storage)

        # set cosigner master privkey
        cosigner_master_privkey = bip32_private_derivation(self.cosigner_root_privkey, "m/", "m/1491'/0'")[0]
        self.cosigner_master_pubkey = xpub_from_xprv(cosigner_master_privkey)

        self.wallet.set_chain("BTC")
        self.wallet.add_seed(self.seed_text, self.password)
        self.wallet.create_master_keys(self.password)
        self.wallet.add_master_public_key("x2/", self.cosigner_master_pubkey)
        self.wallet.create_main_account(self.password)

    def _switch_chain(self, chaincode):
        self.wallet.set_chain(chaincode)
        action = self.wallet.get_action()
        while action is not None:
            if action == 'add_chain':
                self.wallet.create_master_keys(self.password)
            elif action == 'create_accounts':
                self.wallet.create_main_account(self.password)
            action = self.wallet.get_action()

    def test_wallet_seed(self):
        self.assertEqual(self.wallet.get_seed(self.password), self.seed_text)

    def test_wallet_root_derivation(self):
        self.wallet.set_chain('BTC')
        self.assertEqual(bip32_root(self.wallet.mnemonic_to_seed(self.seed_text, ''))[0],
            self.actual_root_privkey)

    def test_master_pubkey_derivation(self):
        self.assertEqual('xpub6B48x5PF7WJ73D9TvyEWFJpPgXxp1qVS8RVGttATwxvAmsfShE7sCGTME3D5SDDQAQtVwDQFLSAXYqxHtFix1LufTs3uEJwTRxfL9wJNp3s',
            self.wallet.master_public_keys.get("x1/"))
        self.assertEqual('xpub6ASQmDxzepDJ5i7fQgURxGfgFDEcWPNrjkEqFWYhkUEjAmKpBgj1Kbtt1tSRfYBBU11SJLDhU5HSjZSKNeY3o7t85ESDJAgFcPsEfVCBrSF',
            self.wallet.master_public_keys.get("x2/"))

    def test_chain_pubkey_derivation(self):
        account_master_pubkeys = self.wallet.accounts["0"].get_master_pubkeys()
        x1_btc_pubkey = bip32_public_derivation(self.wallet.master_public_keys.get("x1/"), "", "/0")
        self.assertEqual('xpub6CfssEAJDCoTHU922RJy8oyXkdPNP8sMFxorzG9ncAbZjZRKCq5NFdRVybzvqHSPntpRDfHtGErXPbk1Y9uAJGJLZFtscVCMZP7mnRFqyQX',
            account_master_pubkeys[0])
        x2_btc_pubkey = bip32_public_derivation(self.wallet.master_public_keys.get("x2/"), "", "/0")
        self.assertEqual('xpub6Ckpjg1oUbAUwXAChU3eWAovMZTWmdMLFskZvRbVTbd8QNM5XG1WdBDubzFAkJjMMktsRRyyzhNKPuYaGNgroYuaz8R3fCGiLWBvmbXX1F2',
            account_master_pubkeys[1])

        # switch chains
        self._switch_chain("MZC")
        account_master_pubkeys = self.wallet.accounts["0"].get_master_pubkeys()
        x1_mzc_pubkey = bip32_public_derivation(self.wallet.master_public_keys.get("x2/"), "", "/13")
        self.assertEqual('xpub6CfssEAJDCoTrhLTgjvQU5PYkwT81bBvuBsnVJ1eP2XDxhNLfbVDHC8G9kxwcSpAtGFEoLqkUrz64nV59kV8fDqkFc3xjn6nUbtiwmQzrRe',
            account_master_pubkeys[0])
        x2_mzc_pubkey = bip32_public_derivation(self.wallet.master_public_keys.get("x2/"), "", "/13")
        self.assertEqual('xpub6Ckpjg1oUbAVWUPSbpbSkNEieqQyxnFCbJG2EnR6AnZUZWuxD6WCDwVQScUaLcUHmbBEuJfM8HCw912QXNGN9FHLQzzPgvsnxMt1YTzbeys',
            account_master_pubkeys[1])

    def test_p2sh_address_creation(self):
        x1_first_btc_key = bip32_public_derivation(self.wallet.master_public_keys.get("x1/"), "", "/0/0/0")
        x2_first_btc_key = bip32_public_derivation(self.wallet.master_public_keys.get("x2/"), "", "/0/0/0")
        x_pubkeys = [x1_first_btc_key, x2_first_btc_key]
        raw_pubkeys = map( lambda x: deserialize_xkey(x)[4], x_pubkeys )
        pubkeys = map( lambda x: x.encode('hex'), raw_pubkeys )

        # Compare redeem script to manually calculated one
        redeem_script = multisig_script(sorted(pubkeys), 2)
        self.assertEqual('522102ee780aa224c9fe54caff984205077b7cca08ced3188a3f3c639d83deda6b9a592103124429ddbed55593d0abea0d0d3d283eca4546e40017b2945f4666c561b494ba52ae',
            redeem_script)

        p2sh_addr = hash_160_to_bc_address( hash_160(redeem_script.decode('hex')), self.wallet.active_chain.p2sh_version )
        self.assertEqual('3MqemPAHZDGLr537QBvU7i4dRFY3Xvad7X', p2sh_addr)

        # switch chains
        self._switch_chain("MZC")
        x1_first_mzc_key = bip32_public_derivation(self.wallet.master_public_keys.get("x1/"), "", "/13/0/0")
        x2_first_mzc_key = bip32_public_derivation(self.wallet.master_public_keys.get("x2/"), "", "/13/0/0")
        x_pubkeys = [x1_first_mzc_key, x2_first_mzc_key]
        raw_pubkeys = map( lambda x: deserialize_xkey(x)[4], x_pubkeys )
        pubkeys = map( lambda x: x.encode('hex'), raw_pubkeys )

        # Compare redeem script to manually calculated one
        redeem_script = multisig_script(sorted(pubkeys), 2)
        self.assertEqual('5221027bdb7f5c42096580442e63235434bcc9ddf9689bbeb917705cd0edf9c6e264292102919725862f59a43274443ea11d7a8e25c15147213dcb6186c24d8629d37d6d8d52ae',
            redeem_script)

        p2sh_addr = hash_160_to_bc_address( hash_160(redeem_script.decode('hex')), self.wallet.active_chain.p2sh_version )
        self.assertEqual('4jjXnsGuWLH3YgnagWH12kK7HjDtsBv8SQ', p2sh_addr)


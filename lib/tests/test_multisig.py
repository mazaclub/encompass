import shutil
import tempfile
import sys
import unittest

from StringIO import StringIO
from lib.bitcoin import bip32_root, bip32_private_derivation, bip32_public_derivation, xpub_from_xprv, deserialize_xkey, hash_160, hash_160_to_bc_address
from lib.wallet import WalletStorage, Wallet_2of2
from lib import chainparams
from lib.transaction import Transaction


class FakeConfig(object):
    """A stub config file to be used in tests"""
    def __init__(self, path):
        self.path = path
        self.store = {}

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
        redeem_script = Transaction.multisig_script(sorted(pubkeys), 2)
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
        redeem_script = Transaction.multisig_script(sorted(pubkeys), 2)
        self.assertEqual('5221027bdb7f5c42096580442e63235434bcc9ddf9689bbeb917705cd0edf9c6e264292102919725862f59a43274443ea11d7a8e25c15147213dcb6186c24d8629d37d6d8d52ae',
            redeem_script)

        p2sh_addr = hash_160_to_bc_address( hash_160(redeem_script.decode('hex')), self.wallet.active_chain.p2sh_version )
        self.assertEqual('4jjXnsGuWLH3YgnagWH12kK7HjDtsBv8SQ', p2sh_addr)


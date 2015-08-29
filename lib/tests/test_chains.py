import shutil
import tempfile
import sys
import unittest

from StringIO import StringIO
from lib import bitcoin, base58
from lib.bitcoin import bip32_root, bip32_private_derivation
from lib.wallet import WalletStorage, NewWallet
from lib import chainparams


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

class TestNewWallet(WalletTestCase):

    seed_text = "travel nowhere air position hill peace suffer parent beautiful rise blood power home crumble teach"
    password = "secret"

    # mnemonic_to_seed should be this
    actual_root_privkey = 'xprv9s21ZrQH143K3cU1yF5gBUQqHw8QBnH5Cgym3XqSRZmfSJ3J2NYzjd7UcdHwjwBjKXD3ZvwoMLo88F4oaVhYgZZ5SdmZ9RA9Wdf93U8iZB3'


    def setUp(self):
        super(TestNewWallet, self).setUp()
        self.storage = WalletStorage(self.fake_config)
        self.wallet = NewWallet(self.storage)
        # This cannot be constructed by electrum at random, it should be safe
        # from eventual collisions.
        self.wallet.add_seed(self.seed_text, self.password)
        self.wallet.create_master_keys(self.password)
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

    def test_wallet_key_derivation(self):
        self._switch_chain('BTC')
        # master key for Bitcoin (m/44'/0')
        self.assertEqual('xprv9wrjoAEFgZU867r47BZXNvdM6y3w4DHnRnWiRq95DHV2u6SQ19LJ3NVe3vjhz5BQdPrZTTdQo7iGhVXLsVz1ysDBa9K94tXJFkNif39ESue',
            self.wallet.get_master_private_key("x/", self.password) )

        # key for Bitcoin account 0 (m/44'/0'/0')
        self.assertEqual('xprv9yARpU9jbs62FabfqwhqH4ZhsaMEeyuzvNc97nBDk54TTxbkuwqkiEYy8wrYFQcwZUDzKD3RaFdbJYVYWLBiXyELgiWBRw4cdvGQ2CPK3FD',
            self.wallet.get_master_private_key("x/0'", self.password) )

        self._switch_chain('MZC')
        # master key for Mazacoin (m/44'/13')
        self.assertEqual('xprv9wrjoAEFgZU8dr6gc32HuUXAGwfULLtaFHZGy5L5MQfXSRK3cGyUKhnDtejWKxyPk15PWt3SRR68v6TBZog6jj1yvJTssVb7NyM1zZrPBsp',
            self.wallet.get_master_private_key("x/", self.password) )

        # key for Mazacoin account 0 (m/44'/13'/0')
        self.assertEqual('xprv9zT9DPHrjeZS4gUXt9dwZfrTzWAyBsBAHatw3vthKUbqAMo8Z15NQq7zBU6tWrEp6Wk6Tk4o9NNaRz9dNbSRHkP1TcrKotKRk2TcZF1647w',
            self.wallet.get_master_private_key("x/0'", self.password) )

    def test_update_password(self):
        # Switch to Mazacoin and verify that the other chain is also updated with a new password
        new_password = "secret2"
        self._switch_chain('BTC')
        self._switch_chain('MZC')
        self.wallet.update_password(self.password, new_password)

        # master key for Mazacoin (m/44'/13')
        self.assertEqual('xprv9wrjoAEFgZU8dr6gc32HuUXAGwfULLtaFHZGy5L5MQfXSRK3cGyUKhnDtejWKxyPk15PWt3SRR68v6TBZog6jj1yvJTssVb7NyM1zZrPBsp',
            self.wallet.get_master_private_key("x/", new_password) )

        self._switch_chain('BTC')
        # master key for Bitcoin (m/44'/0')
        self.assertEqual('xprv9wrjoAEFgZU867r47BZXNvdM6y3w4DHnRnWiRq95DHV2u6SQ19LJ3NVe3vjhz5BQdPrZTTdQo7iGhVXLsVz1ysDBa9K94tXJFkNif39ESue',
            self.wallet.get_master_private_key("x/", new_password) )


class ChainsBase58Test(unittest.TestCase):

    def setUp(self):
        super(ChainsBase58Test, self).setUp()
        chainparams.set_active_chain('BTC')

class TestChainsBase58(ChainsBase58Test):

    def setUp(self):
        super(TestChainsBase58, self).setUp()
        self.masterkey = 'xprv9s21ZrQH143K2AyWpResEyFfXb4J8BDDjUfG9WH7Q199E91HvHnPMM33yxLBFMcDe61QKRZvAiVLWLhxnRQg9pvGPvK7Acca3V9CZ21KSY9'
        self.privkey = bitcoin.deserialize_xkey(self.masterkey)[4]

    def test_wif_encoding(self):
        active_chain = chainparams.get_active_chain()
        wif = base58.SecretToASecret(self.privkey, compressed=True, addrtype = active_chain.wif_version)
        self.assertEqual('L3PoHZXjsvP91C8WuyiwzYKgjzthZD2Q39Wzrwfsndov6Cwcu8zX', wif)

        addr = bitcoin.address_from_private_key(wif, addrtype = active_chain.p2pkh_version, wif_version = active_chain.wif_version)
        self.assertEqual('1599aBMAHbgEkf4dzvd9jxBFgVyufZVVc1', addr)

        chainparams.set_active_chain('MZC')
        active_chain = chainparams.get_active_chain()
        wif = base58.SecretToASecret(self.privkey, compressed=True, addrtype = active_chain.wif_version)
        self.assertEqual('aF4LB486ggLLYsQG1FcgRFQSdiBKhP4BfZKWaYvxvaAF7z6MGkAG', wif)

        addr = bitcoin.address_from_private_key(wif, addrtype = active_chain.p2pkh_version, wif_version = active_chain.wif_version)
        self.assertEqual('MC3JocFZncr3eL2yDuH5zDnb9is5GUzUJv', addr)


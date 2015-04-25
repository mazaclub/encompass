import shutil
import tempfile
import sys
import unittest

from StringIO import StringIO
from lib.bitcoin import bip32_root, bip32_private_derivation, bip32_public_derivation, xpub_from_xprv, deserialize_xkey, hash_160, hash_160_to_bc_address, int_to_hex, DecodeBase58Check
from lib.account import BIP32_Account
from lib.wallet import WalletStorage, Wallet_2of2, Wallet_MofN
from lib import chainparams
from lib.transaction import Transaction


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
        cosigner1_master_privkey = bip32_private_derivation(self.cosigner1_root_privkey, "m/", "m/44'/0'")[0]
        self.cosigner1_master_pubkey = xpub_from_xprv(cosigner1_master_privkey)

        cosigner2_master_privkey = bip32_private_derivation(self.cosigner2_root_privkey, "m/", "m/44'/0'")[0]
        self.cosigner2_master_pubkey = xpub_from_xprv(cosigner2_master_privkey)

        cosigner3_master_privkey = bip32_private_derivation(self.cosigner3_root_privkey, "m/", "m/44'/0'")[0]
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
        self.assertEqual('xpub6Ar6Cfm9Ww2RJbvXDD6Xk4a5eztRTg1do1SKEDYgmd21mtmYYgeYbAp7uCKYMgVfezCLTpM2rn25Ma5Vhm5pRktzM1cspx9MQwMJNs21Tjm',
            self.wallet.master_public_keys.get("x1/"))
        self.assertEqual('xpub6AEE1YapfdwPEwJNWLm1gz7CLSiXXEWD58TqKf7vCk8ZrXmdVi1NuKjQvms34eYNFUdRhpP2TJuwPwvFv7BybfTfZwkKZ7k444ucyDTZfLS',
            self.wallet.master_public_keys.get("x2/"))
        self.assertEqual('xpub6BHS4GK2qnTck8CHgg8dfBgLb4xyenXZHyhK9Wuf7Syr86CMTvXZ81JMwQbSVA1zGcBMtjqZpaLhVS3j8JM82V9DqSwmnYoMWTFNhyULpXQ',
            self.wallet.master_public_keys.get("x3/"))
        self.assertEqual('xpub6Ayb2onGrr2be263MzJSXsVHgBZJYUYZDuaA2JJbsKafQEnXpegWC4dJY7tELcJm1tWWv4AhwJaC2jGQU6aMELtGDw6QEwK1UhiyHjyFQnx',
            self.wallet.master_public_keys.get("x4/"))

    def test_account(self):
        acc = self.wallet.accounts["0"]
        pubkeys = acc.get_master_pubkeys()
        self.assertIn('xpub6C9nDygV6a7MK6XaEYWHEwPdFmy6MtqvYPgLVae2Pqns4X9bgQtEEBppTBbLotCgtSkBdauqRG4QCibdCsvScECZzmNQmH1M44s6XNWSntA', pubkeys)
        self.assertIn('xpub6BySj5mtu9kXBkahhpjjHjtxv2zWn87wWCL6zMJkshiBov9Drpzs54aNT1TuvMtgDtsfFapm6QiYmWw6R3CK2WAZo6NqCxWnsUWPApqmsv9', pubkeys)
        self.assertIn('xpub6DVbRUbTRwQmSNa9eLtKMWuP5dbHBVvtkuWzWENYKHp33Vsvuu2KZ5EQjdToEzvWYfHj6k5JCoeeMv1gzjc8VZc2TePXGV9m1N3bYM6VdPa', pubkeys)
        self.assertIn('xpub6DVMDNati9BXsp3B4XFakHn2p9SoAjZGhYYYiRXAwJkNypy5fPseuG1g7BHC7s4myjL4XRPi5xKmQHH9UnQYt1x3tSxVQEAJFB8G69mDW4X', pubkeys)

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
        redeem_script = Transaction.multisig_script(sorted(pubkeys), acc.multisig_m)
        self.assertEqual('5321032cc19685978bba02960adca60eec2f564126a4d4582f16b0b50a6e6cf17168a02103646ea928844710efcdba31b616aa9e97c6bcdac15a40d96a98cb7833e1848286210378568d703b6c64c9f4e3bd90b3c79c7e174b733629ca83c2c1456c5ddfc229792103f1c2170673eda7023e16813f8dc2b459c18d17520cfab0603ed1695a8e15a79d54ae', redeem_script)
        p2sh_addr = hash_160_to_bc_address( hash_160(redeem_script.decode('hex')), self.wallet.active_chain.p2sh_version )
        self.assertEqual("32SbQbBthcMzRSpCw1ifAXqWviJGH5HKUk", p2sh_addr)

    def test_transaction(self):

        wallet_keys = {
            'xpub6Gyz3Cuftr7dDPqWN54hcVjV4GuNzpWoAbPsUr493ReaaoAuFHk6A19MHgtuRnwEMPBhWFhGf9vMPX956n9zzgqRfS3oYzM9MFUSq7K3Dsv': 'L4g1Lj4jGLTpb2Zmbs23sMmvMmNaAySYEoaYpjopzzx2rMc48Why',
            'xpub6FYJARMLJMUwitvXrJThC9yCxhFpuMcFTCkrcnLvww98UrZSNjLsK9RcsDt7qGW8rXmBjr2VFGYth3TTPRvefszUGfmbeWiJBX6wLtgPtzZ': 'L4NeeK7GB8iepbsSvR9edFgKRM6kpbATaoH8JVD3uVMdaicEAYb3',
            'xpub6GfJ2THHDLsQTwzhjmUfmYyKj7CELnfbXuzZdbwCtC8h7NNHnHmdSrPWRP6fW12kQFo71k4qr2E9urmVk95WCT2oRg9CrCHT49CAsB6MAoR': 'KwJQLb8Qem1QTbgpcUBCVGchqi71RBG5TeJXjHNNW5XEDqeJY1wk'
#            'xpub6GiSmJrVQC5q2m5cRcZvUgnGUsfeEqi3eEfUTgacnA33G8PAQnJeeMzpNAGUA9JL3goUui7BY52rVPwhmxMALkmFh5ZuwJDKrPv8ERkG3CK': 'L3jUPoR7fUwB9mwfuqqF79mHDpj5rpygQhdWntJ9ShZ9nbyRab5h'
        }

        acc = self.wallet.accounts["0"]
        redeem_script = '5321032cc19685978bba02960adca60eec2f564126a4d4582f16b0b50a6e6cf17168a02103646ea928844710efcdba31b616aa9e97c6bcdac15a40d96a98cb7833e1848286210378568d703b6c64c9f4e3bd90b3c79c7e174b733629ca83c2c1456c5ddfc229792103f1c2170673eda7023e16813f8dc2b459c18d17520cfab0603ed1695a8e15a79d54ae'

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
        self.assertEqual('0100000001111111111111111111111111111111111111111111111111111111111111111100000000fd6801004730440220597dd6ff2d2eebc4699529404e06512204ca9e8074a252bc2746c9d1059888b902207d4ce0ae33b1d5762dbe74a1bbfd6282443277206f1ed35286c7b8eb0e1001230148304502207d036628f6af1d4fcb21bc743d3a3c9d05a9999ee767a9ce4f4eb0cce7c2ac74022100c7bda5b1e7b7767ce80fedeabcfb09460dbbfa28197016ac9ac8e5bf0c2333fe01483045022100bc99a007249424b2296f72c5de82f5205fe0331d68d39599ad0ab7d2356926bc0220227c4a0016b6a6cd7bf544666f88bafc4a3112e8905571e19720d1883927f756014c8b5321032cc19685978bba02960adca60eec2f564126a4d4582f16b0b50a6e6cf17168a02103646ea928844710efcdba31b616aa9e97c6bcdac15a40d96a98cb7833e1848286210378568d703b6c64c9f4e3bd90b3c79c7e174b733629ca83c2c1456c5ddfc229792103f1c2170673eda7023e16813f8dc2b459c18d17520cfab0603ed1695a8e15a79d54aeffffffff0120a10700000000001976a914fc03ab7c28d17349f084f7cadde4dafc356918d388ac00000000', str(tx))

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
        cosigner_master_privkey = bip32_private_derivation(self.cosigner_root_privkey, "m/", "m/44'/0'")[0]
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
        self.assertEqual('xpub6Ar6Cfm9Ww2RJbvXDD6Xk4a5eztRTg1do1SKEDYgmd21mtmYYgeYbAp7uCKYMgVfezCLTpM2rn25Ma5Vhm5pRktzM1cspx9MQwMJNs21Tjm',
            self.wallet.master_public_keys.get("x1/"))
        self.assertEqual('xpub6AEE1YapfdwPEwJNWLm1gz7CLSiXXEWD58TqKf7vCk8ZrXmdVi1NuKjQvms34eYNFUdRhpP2TJuwPwvFv7BybfTfZwkKZ7k444ucyDTZfLS',
            self.wallet.master_public_keys.get("x2/"))

    def test_chain_pubkey_derivation(self):
        account_master_pubkeys = self.wallet.accounts["0"].get_master_pubkeys()
        x1_btc_pubkey = bip32_public_derivation(self.wallet.master_public_keys.get("x1/"), "", "/0")
        self.assertEqual('xpub6C9nDygV6a7MK6XaEYWHEwPdFmy6MtqvYPgLVae2Pqns4X9bgQtEEBppTBbLotCgtSkBdauqRG4QCibdCsvScECZzmNQmH1M44s6XNWSntA',
            account_master_pubkeys[0])
        x2_btc_pubkey = bip32_public_derivation(self.wallet.master_public_keys.get("x2/"), "", "/0")
        self.assertEqual('xpub6BySj5mtu9kXBkahhpjjHjtxv2zWn87wWCL6zMJkshiBov9Drpzs54aNT1TuvMtgDtsfFapm6QiYmWw6R3CK2WAZo6NqCxWnsUWPApqmsv9',
            account_master_pubkeys[1])

        # switch chains
        self._switch_chain("MZC")
        account_master_pubkeys = self.wallet.accounts["0"].get_master_pubkeys()
        x1_mzc_pubkey = bip32_public_derivation(self.wallet.master_public_keys.get("x2/"), "", "/13")
        self.assertEqual('xpub6C9nDygV6a7MsNcyFHFPkCG744MxEpuW397D948jYaYTcssA5AABS8z4EX6qkvoo32eYujjMCPeaKPevYnWSrmiSdV3yiDdXDd9QNQqsULb',
            account_master_pubkeys[0])
        x2_mzc_pubkey = bip32_public_derivation(self.wallet.master_public_keys.get("x2/"), "", "/13")
        self.assertEqual('xpub6BySj5mtu9kXkB96DBREwNgZnqTMSKwfSKPeHtDHQsC5Tjf3QktFvbahyoXns7sxjUr5dvFdH8HjaaaXb75sT3iVwfdHDhX7Tsw4TnT549q',
            account_master_pubkeys[1])

    def test_p2sh_address_creation(self):
        x1_first_btc_key = bip32_public_derivation(self.wallet.master_public_keys.get("x1/"), "", "/0/0/0")
        x2_first_btc_key = bip32_public_derivation(self.wallet.master_public_keys.get("x2/"), "", "/0/0/0")
        x_pubkeys = [x1_first_btc_key, x2_first_btc_key]
        raw_pubkeys = map( lambda x: deserialize_xkey(x)[4], x_pubkeys )
        pubkeys = map( lambda x: x.encode('hex'), raw_pubkeys )

        # Compare redeem script to manually calculated one
        redeem_script = Transaction.multisig_script(sorted(pubkeys), 2)
        self.assertEqual('52210378568d703b6c64c9f4e3bd90b3c79c7e174b733629ca83c2c1456c5ddfc229792103f1c2170673eda7023e16813f8dc2b459c18d17520cfab0603ed1695a8e15a79d52ae',
            redeem_script)

        p2sh_addr = hash_160_to_bc_address( hash_160(redeem_script.decode('hex')), self.wallet.active_chain.p2sh_version )
        self.assertEqual('32GTArvFYGWdQXCTPZruE96qtmi6jCLh19', p2sh_addr)

        # switch chains
        self._switch_chain("MZC")
        x1_first_mzc_key = bip32_public_derivation(self.wallet.master_public_keys.get("x1/"), "", "/13/0/0")
        x2_first_mzc_key = bip32_public_derivation(self.wallet.master_public_keys.get("x2/"), "", "/13/0/0")
        x_pubkeys = [x1_first_mzc_key, x2_first_mzc_key]
        raw_pubkeys = map( lambda x: deserialize_xkey(x)[4], x_pubkeys )
        pubkeys = map( lambda x: x.encode('hex'), raw_pubkeys )

        # Compare redeem script to manually calculated one
        redeem_script = Transaction.multisig_script(sorted(pubkeys), 2)
        self.assertEqual('5221036bf599d52ff5b0e680e83b2f03884285829cfb7bf979869884103e7a5b52e1e32103b4cadb818f1bd76f79564496e0199335e25cebcf0d26b60d9d0f39721028e51a52ae',
            redeem_script)

        p2sh_addr = hash_160_to_bc_address( hash_160(redeem_script.decode('hex')), self.wallet.active_chain.p2sh_version )
        self.assertEqual('4s7Z2JSWS54Q9chXp8fDvifiXhxiwbX2oN', p2sh_addr)


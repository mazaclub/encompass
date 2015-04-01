import unittest
from lib import bitcoin
from lib import chainparams

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
        wif = bitcoin.SecretToASecret(self.privkey, compressed=True, addrtype = active_chain.wif_version)
        self.assertEqual('L3PoHZXjsvP91C8WuyiwzYKgjzthZD2Q39Wzrwfsndov6Cwcu8zX', wif)

        addr = bitcoin.address_from_private_key(wif, addrtype = active_chain.p2pkh_version, wif_version = active_chain.wif_version)
        self.assertEqual('1599aBMAHbgEkf4dzvd9jxBFgVyufZVVc1', addr)

        chainparams.set_active_chain('MZC')
        active_chain = chainparams.get_active_chain()
        wif = bitcoin.SecretToASecret(self.privkey, compressed=True, addrtype = active_chain.wif_version)
        self.assertEqual('aF4LB486ggLLYsQG1FcgRFQSdiBKhP4BfZKWaYvxvaAF7z6MGkAG', wif)

        addr = bitcoin.address_from_private_key(wif, addrtype = active_chain.p2pkh_version, wif_version = active_chain.wif_version)
        self.assertEqual('MC3JocFZncr3eL2yDuH5zDnb9is5GUzUJv', addr)

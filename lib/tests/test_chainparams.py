import unittest
from lib import chainparams

class ChainParamsTestCase(unittest.TestCase):

    def setUp(self):
        super(ChainParamsTestCase, self).setUp()
        chainparams.set_active_chain('BTC')

    def tearDown(self):
        super(ChainParamsTestCase, self).tearDown()

class TestChainParams(ChainParamsTestCase):

    def test_get_active_chain(self):
        chainparams.set_active_chain('MZC')
        chain = chainparams.get_active_chain()
        self.assertEqual(13, chain.chain_index)
        self.assertEqual('Mazacoin', chain.coin_name)
        self.assertEqual('MZC', chain.code)
        self.assertEqual(50, chain.p2pkh_version)
        self.assertEqual(9, chain.p2sh_version)
        self.assertEqual(224, chain.wif_version)

        chainparams.set_active_chain('BTC')
        chain = chainparams.get_active_chain()
        self.assertEqual(0, chain.chain_index)
        self.assertEqual('Bitcoin', chain.coin_name)
        self.assertEqual('BTC', chain.code)
        self.assertEqual(0, chain.p2pkh_version)
        self.assertEqual(5, chain.p2sh_version)
        self.assertEqual(128, chain.wif_version)

    def test_set_active_chain(self):
        chainparams.set_active_chain('MZC')

    def test_is_known_chain(self):
        self.assertEqual(True, chainparams.is_known_chain('BTC'))
        self.assertEqual(False, chainparams.is_known_chain('FOOBAR'))

    def test_get_params(self):
        chainparams.set_active_chain('MZC')
        params = chainparams.get_params('MZC')
        self.assertEqual(13, params.chain_index)
        self.assertEqual('Mazacoin', params.coin_name)
        self.assertEqual('MZC', params.code)
        self.assertEqual('mazacoin', params.module_name)

        params = chainparams.get_params('BTC')
        self.assertEqual(0, params.chain_index)
        self.assertEqual('Bitcoin', params.coin_name)
        self.assertEqual('BTC', params.code)
        self.assertEqual('bitcoin', params.module_name)

    def test_get_chainparam(self):
        chainparams.set_active_chain('MZC')
        self.assertEqual('Mazacoin', chainparams.get_chainparam('MZC', 'coin_name'))
        self.assertEqual('mazacoin', chainparams.get_chainparam('MZC', 'module_name'))
        self.assertEqual('Bitcoin', chainparams.get_chainparam('BTC', 'coin_name'))
        self.assertEqual('bitcoin', chainparams.get_chainparam('BTC', 'module_name'))

    def test_get_chain_index(self):
        chainparams.set_active_chain('MZC')
        index = chainparams.get_chain_index('MZC')
        self.assertEqual(13, index)
        index = chainparams.get_chain_index('BTC')
        self.assertEqual(0, index)

    def test_get_code_from_index(self):
        chainparams.set_active_chain('MZC')
        code = chainparams.get_code_from_index(13)
        self.assertEqual('MZC', code)
        code = chainparams.get_code_from_index(0)
        self.assertEqual('BTC', code)

    def test_all_chainkey_modules(self):
        all_chains = chainparams._known_chains
        for params in all_chains:
            chain = chainparams.get_chain_instance(params.code)
            # ensure params data is correct
            self.assertEqual(params.chain_index, chain.chain_index)
            self.assertEqual(params.coin_name, chain.coin_name)
            self.assertEqual(params.code, chain.code)

            ##  sanity-test chainkey module data ##
            # constants
            self.assertGreaterEqual(chain.chain_index, 0)
            self.assertGreaterEqual(chain.p2pkh_version, 0)
            self.assertGreaterEqual(chain.p2sh_version, 0)
            self.assertGreaterEqual(chain.wif_version, 0)
            self.assertGreaterEqual(chain.DUST_THRESHOLD, 0)
            self.assertGreaterEqual(chain.MIN_RELAY_TX_FEE, 0)
            self.assertGreaterEqual(chain.RECOMMENDED_FEE, 0)
            self.assertGreaterEqual(chain.COINBASE_MATURITY, 0)
            # collections
            self.assertGreaterEqual(len(chain.block_explorers), 1)
            self.assertGreaterEqual(len(chain.DEFAULT_SERVERS), 1)
            # there must be a unit with 8 decimal places since that's the default
            self.assertGreaterEqual(len(chain.base_units), 1)
            self.assertIn(8, chain.base_units.values())

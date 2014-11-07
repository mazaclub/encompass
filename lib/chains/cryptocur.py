'''The abstract class for a cryptocurrency.'''

import chainparams

class CryptoCur(object):
    '''Abstract class containing cryptocurrency-specific code'''

    # index used in child key derivation
    chain_index = 0
    # Full name (e.g. Bitcoin)
    coin_name = ''
    # Abbreviation (e.g. BTC)
    code = ''
    # Address base58 prefix
    p2pkh_version = 0
    # Script hash base58 prefix
    p2sh_version = 0
    # Private key base58 prefix
    wif_version = 0
    # Extended pubkey base58 prefix
    ext_pub_version = ''
    # Extended privkey base58 prefix
    ext_priv_version = ''

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 1000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 100

    def get_next_target(self):
        pass

    

'''Chain-specific Bitcoin code'''
from cryptocur import CryptoCur

class Bitcoin(CryptoCur):
    chain_index = 0
    coin_name = 'Bitcoin'
    code = 'BTC'
    p2pkh_version = 0
    p2sh_version = 5
    wif_version = 128
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 1000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 100

'''Chain-specific Mazacoin code'''
from cryptocur import CryptoCur

class Mazacoin(CryptoCur):
    chain_index = 1 # CHANGE THIS after registration
    coin_name = 'Mazacoin'
    code = 'MZC'
    p2pkh_version = 50
    p2sh_version = 9
    wif_version = 224
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 1000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 100

'''The abstract class for a cryptocurrency.'''

import os, hashlib

hash_encode = lambda x: x[::-1].encode('hex')
hash_decode = lambda x: x.decode('hex')[::-1]

def rev_hex(s):
    return s.decode('hex')[::-1].encode('hex')

def int_to_hex(i, length=1):
    s = hex(i)[2:].rstrip('L')
    s = "0"*(2*length - len(s)) + s
    return rev_hex(s)

def sha256(x):
    return hashlib.sha256(x).digest()

def Hash(x):
    if type(x) is unicode: x=x.encode('utf-8')
    return sha256(sha256(x))
    


class CryptoCur(object):
    '''Abstract class containing cryptocurrency-specific code'''
    ### Chain parameters ###

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

    ### Constants ###

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 1000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 100


    # Block explorers {name : URL}
    block_explorers = {
        'Blockchain.info': 'https://blockchain.info/tx/',
        'Blockr.io': 'https://blockr.io/tx/info/',
        'Insight.is': 'http://live.insight.is/tx/',
        'Blocktrail.com': 'https://www.blocktrail.com/tx/'
    }

    # Currency units {name : decimal point}
    base_units = {
        'COIN': 8,
        'mCOIN': 5
    }

    ### Electrum constants ###

    # Number of headers in one chunk
    chunk_size = 2016

    ### Methods ###


    # Tell us where our blockchain_headers file is
    def set_headers_path(self, path):
        self.headers_path = path

    def path(self):
        return self.headers_path

    def verify_chain(self, chain):
        pass

    def verify_chunk(self, index, hexdata):
        pass

    def header_to_string(self, res):
        pass

    def header_from_string(self, s):
        pass

    def hash_header(self, header):
        pass

    def save_chunk(self, index, chunk):
        pass

    def save_header(self, header):
        pass

    def read_header(self, block_height):
        pass

    # Calculate the difficulty target
    def get_target(self, index, chain=None):
        pass



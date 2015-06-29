'''The base class for a cryptocurrency.'''

import os, hashlib
import coinhash

hash_encode = lambda x: x[::-1].encode('hex')
hash_decode = lambda x: x.decode('hex')[::-1]

def rev_hex(s):
    return s.decode('hex')[::-1].encode('hex')

def int_to_hex(i, length=1):
    s = hex(i)[2:].rstrip('L')
    s = "0"*(2*length - len(s)) + s
    return rev_hex(s)

def bits_to_target(bits):
    """Convert a compact representation to a hex target."""
    MM = 256*256*256
    a = bits%MM
    if a < 0x8000:
        a *= 256
    target = (a) * pow(2, 8 * (bits/MM - 3))
    return target

def target_to_bits(target):
    """Convert a target to compact representation."""
    MM = 256*256*256
    c = ("%064X"%target)[2:]
    i = 31
    while c[0:2]=="00":
        c = c[2:]
        i -= 1

    c = int('0x'+c[0:6],16)
    if c >= 0x800000:
        c /= 256
        i += 1

    new_bits = c + MM * i
    return new_bits


# Chain hook system
#
# This allows the active blockchain to hook into arbitrary functions
# in the same way that plugins do.
chainhook_names = set()
chainhooks = {}

def chainhook(func):
    """As a decorator, this allows blockchains to hook into functions
    that call run_chainhook."""
    n = func.func_name
    if not n in chainhook_names:
        chainhook_names.add(n)
    return func


class CryptoCur(object):
    '''Abstract class containing cryptocurrency-specific code'''
    ### Chain parameters ###

    # Whether this chain verifies Proof-of-Work
    PoW = False

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

    ### Hash Algorithms ###
    base58_hash = coinhash.SHA256dHash
    transaction_hash = coinhash.SHA256dHash

    # Block explorers {name : URL}
    block_explorers = {
        'Blockchain.info': 'https://blockchain.info/tx/',
        'Blockr.io': 'https://blockr.io/tx/info/',
    }

    # Currency units {name : decimal point}
    base_units = {
        'COIN': 8,
        'mCOIN': 5
    }

    ### Electrum constants ###

    # Number of headers in one chunk
    chunk_size = 2016

    # URL where a header bootstrap can be downloaded
    headers_url = ''

    ### Methods ###

    def __init__(self):
        for k in dir(self):
            if k in chainhook_names:
                l = chainhooks.get(k, [])
                if not self.__class__ in l:
                    l.append( self.__class__ )
                chainhooks[k] = l

    # Called on chain reorg. Go back by COINBASE_MATURITY.
    def reorg_handler(self, local_height):
        name = self.path()
        if os.path.exists(name):
            f = open(name, 'rb+')
            f.seek((local_height*80) - (self.COINBASE_MATURITY*80))
            f.truncate()
            f.close()

    # Tell us where our blockchain_headers file is
    def set_headers_path(self, path):
        self.headers_path = path

    def path(self):
        return self.headers_path

    # Called from blockchain.py when a chain of headers (arbitrary number of headers that's less than a chunk) needs verification.
    def verify_chain(self, chain):
        pass

    # Called from blockchain.py when a chunk of headers needs verification.
    def verify_chunk(self, index, hexdata):
        pass

    # Most common header format. Reimplement in a derived class if header format differs.
    def header_to_string(self, res):
        s = int_to_hex(res.get('version'),4) \
            + rev_hex(res.get('prev_block_hash')) \
            + rev_hex(res.get('merkle_root')) \
            + int_to_hex(int(res.get('timestamp')),4) \
            + int_to_hex(int(res.get('bits')),4) \
            + int_to_hex(int(res.get('nonce')),4)
        return s

    # Most common header format. Reimplement in a derived class if header format differs.
    def header_from_string(self, s):
        hex_to_int = lambda s: int('0x' + s[::-1].encode('hex'), 16)
        h = {}
        h['version'] = hex_to_int(s[0:4])
        h['prev_block_hash'] = hash_encode(s[4:36])
        h['merkle_root'] = hash_encode(s[36:68])
        h['timestamp'] = hex_to_int(s[68:72])
        h['bits'] = hex_to_int(s[72:76])
        h['nonce'] = hex_to_int(s[76:80])
        return h

    def hash_header(self, header):
        pass

    # save a chunk of headers to the binary file. Should not need to be reimplemented but can be.
    def save_chunk(self, index, chunk):
        filename = self.path()
        f = open(filename,'rb+')
        f.seek(index * self.chunk_size * 80)
        h = f.write(chunk)
        f.close()

    # save a single header to the binary file. Should not need to be reimplemented but can be.
    def save_header(self, header):
        data = self.header_to_string(header).decode('hex')
        assert len(data) == 80
        height = header.get('block_height')
        filename = self.path()
        f = open(filename,'rb+')
        f.seek(height*80)
        h = f.write(data)
        f.close()

    # read a header from the binary file. Should not need to be reimplemented but can be.
    def read_header(self, block_height):
        name = self.path()
        if os.path.exists(name):
            f = open(name,'rb')
            f.seek(block_height*80)
            h = f.read(80)
            f.close()
            if len(h) == 80:
                h = self.header_from_string(h)
                return h

    # Calculate the difficulty target
    def get_target(self, index, chain=None):
        pass



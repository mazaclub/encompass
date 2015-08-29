'''The base class for a cryptocurrency.'''

import os, hashlib
import coinhash

try:
    from chainkey import util_coin
except Exception:
    from .. import util_coin

hash_encode = lambda x: util_coin.hash_encode(x)
hash_decode = lambda x: util_coin.hash_decode(x)
rev_hex = lambda s: util_coin.rev_hex(s)
int_to_hex = lambda i, length=1: util_coin.int_to_hex(i, length)
var_int = lambda i: util_coin.var_int(i)
op_push = lambda i: util_coin.op_push(i)

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
    header_hash = coinhash.SHA256dHash
    merkle_hash = coinhash.SHA256dHash
    transaction_hash = coinhash.SHA256dHash

    # Block explorers {name : URL}
    block_explorers = {
        'Blockchain.info': 'https://blockchain.info/tx/',
        'Blockr.io': 'https://blockr.io/tx/info/',
    }

    # Currency units {name : decimal point}
    base_units = None

    ### Electrum constants ###

    # Number of headers in one chunk
    chunk_size = 2016

    # URL where a header bootstrap can be downloaded
    headers_url = ''

    # Dictionary of {height: hash} values for sanity checking.
    checkpoints = None

    ### Methods ###

    def __init__(self):
        if self.checkpoints is None: self.checkpoints = {}
        # set base_units if not set
        if self.base_units is None:
            self.base_units = {}
            if self.code:
                self.base_units = {self.code : 8}
        # add chainhooks
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
        """Returns whether a chain of headers is valid."""
        first_header = chain[0]
        prev_header = self.read_header(first_header.get('block_height') - 1)
        # if we don't verify PoW, just check that headers connect by previous_hash
        for header in chain:
            height = header.get('block_height')

            prev_hash = self.hash_header(prev_header)
            if self.PoW:
                bits, target = self.get_target(height, chain)
            _hash = self.hash_header(header)
            try:
                assert prev_hash == header.get('prev_block_hash')
                checkpoint_hash = self.checkpoints.get(height)
                if checkpoint_hash is not None:
                    assert checkpoint_hash == _hash
                if self.PoW:
                    assert bits == header.get('bits')
                    assert int('0x'+_hash,16) < target
            except Exception:
                return False

            prev_header = header

        return True

    # Called from blockchain.py when a chunk of headers needs verification.
    def verify_chunk(self, index, hexdata):
        """Attempts to verify a chunk of headers.

        Does not return a value. This either succeeds
        or throws an error."""
        data = hexdata.decode('hex')
        height = index*self.chunk_size
        num = len(data)/80
        # we form a chain of headers so we don't need to save individual headers
        # in cases where a chain uses recent headers in difficulty calculation.
        chain = []

        if index == 0:
            previous_hash = ("0"*64)
        else:
            prev_header = self.read_header(index*self.chunk_size-1)
            if prev_header is None: raise
            previous_hash = self.hash_header(prev_header)

        # if we don't verify PoW, just check that headers connect by previous_hash
        for i in range(num):
            height = index*self.chunk_size + i
            raw_header = data[i*80:(i+1)*80]
            header = self.header_from_string(raw_header)
            _hash = self.hash_header(header)

            if self.PoW:
                header['block_height'] = height
                chain.append(header)
                bits, target = self.get_target(height, chain)

            checkpoint_hash = self.checkpoints.get(height)
            if checkpoint_hash is not None:
                try:
                    assert checkpoint_hash == _hash
                except Exception:
                    raise CheckpointError(height, checkpoint_hash, _hash)
            assert previous_hash == header.get('prev_block_hash')
            if self.PoW:
                assert bits == header.get('bits')
                assert int('0x'+_hash,16) < target

            previous_header = header
            previous_hash = _hash

        self.save_chunk(index, data)

    # Most common header format. Reimplement in a derived class if header format differs.
    def header_to_string(self, res):
        """Create a serialized string from a header dict."""
        s = int_to_hex(res.get('version'),4) \
            + rev_hex(res.get('prev_block_hash')) \
            + rev_hex(res.get('merkle_root')) \
            + int_to_hex(int(res.get('timestamp')),4) \
            + int_to_hex(int(res.get('bits')),4) \
            + int_to_hex(int(res.get('nonce')),4)
        return s

    # Most common header format. Reimplement in a derived class if header format differs.
    def header_from_string(self, s):
        """Create a header dict from a serialized string."""
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
        return rev_hex(( getattr(coinhash, self.header_hash.__name__)(self.header_to_string(header).decode('hex')) ).encode('hex'))

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
    def get_target(self, height, chain=None):
        pass



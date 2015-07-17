'''Chain-specific Viacoin code'''

############################################
# Code here is taken from Vialectrum       #
# https://github.com/vialectrum/vialectrum #
############################################

from cryptocur import CryptoCur, hash_encode, hash_decode, rev_hex, int_to_hex
import os

from coinhash import SHA256dHash, ScryptHash

class Viacoin(CryptoCur):
    PoW = False
    chain_index = 14
    coin_name='Viacoin'
    code = 'VIA'
    p2pkh_version = 71
    p2sh_version = 33
    wif_version = 199
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'

    DUST_THRESHOLD = 0
    MIN_RELAY_TX_FEE = 100000
    RECOMMENDED_FEE = MIN_RELAY_TX_FEE
    COINBASE_MATURITY = 3600

    block_explorers = {
        'explorer.viacoin.org': 'http://explorer.viacoin.org/tx/',
        'bchain.info': 'https://bchain.info/VIA/tx/'
    }

    base_units = {
        'VIA': 8,
        'mVIA': 5,
        'bits': 2
    }

    chunk_size = 2016

    headers_url = 'http://headers.vialectrum.org/blockchain_headers'

    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'server.vialectrum.org': DEFAULT_PORTS,
        'vialectrum.viacoin.net': DEFAULT_PORTS,
    }

    checkpoints = {
        0: "4e9b54001f9976049830128ec0331515eaabe35a70970d79971da1539a400ba1",
        44606: "5ceeec38564a36ee3e1e5404970f5715efe0420e92c8e92bedfdfef782c49320",
    }

    def verify_chain(self, chain):

        first_header = chain[0]
        prev_header = self.read_header(first_header.get('block_height') -1)

        for header in chain:

            height = header.get('block_height')

            prev_hash = self.hash_header(prev_header)
            #bits, target = self.get_target(height/2016, chain)
            _hash = self.pow_hash_header(header)
            try:
                assert prev_hash == header.get('prev_block_hash')
                #assert bits == header.get('bits')
                #assert int('0x'+_hash,16) < target
            except Exception:
                return False

            prev_header = header

        return True

    def verify_chunk(self, index, hexdata):
        data = hexdata.decode('hex')
        height = index*2016
        num = len(data)/80

        if index == 0:
            previous_hash = ("0"*64)
        else:
            prev_header = self.read_header(index*2016-1)
            if prev_header is None: raise
            previous_hash = self.hash_header(prev_header)

        #bits, target = self.get_target(index)

        for i in range(num):
            height = index*2016 + i
            raw_header = data[i*80:(i+1)*80]
            header = self.header_from_string(raw_header)
            _hash = self.pow_hash_header(header)
            assert previous_hash == header.get('prev_block_hash')
            #assert bits == header.get('bits')
            #assert int('0x'+_hash,16) < target

            previous_header = header
            previous_hash = self.hash_header(header)

        self.save_chunk(index, data)

    def hash_header(self, header):
        return rev_hex(SHA256dHash(self.header_to_string(header).decode('hex')).encode('hex'))

    def pow_hash_header(self, header):
        return rev_hex(ScryptHash(self.header_to_string(header).decode('hex')).encode('hex'))

    def get_target(self, index, chain=None):
        if chain is None:
            chain = []  # Do not use mutables as default values!

        max_target = 0x00000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        if index == 0: return 0x1e0ffff0, 0x00000FFFF0000000000000000000000000000000000000000000000000000000

        # Viacoin: go back the full period unless it's the first retarget
        if index == 1:
            first = self.read_header(0)
        else:
            first = self.read_header((index-1)*2016-1)
        last = self.read_header(index*2016-1)
        if last is None:
            for h in chain:
                if h.get('block_height') == index*2016-1:
                    last = h

        nActualTimespan = last.get('timestamp') - first.get('timestamp')
        nTargetTimespan = 84*60*60
        nActualTimespan = max(nActualTimespan, nTargetTimespan/4)
        nActualTimespan = min(nActualTimespan, nTargetTimespan*4)

        bits = last.get('bits')
        # convert to bignum
        MM = 256*256*256
        a = bits%MM
        if a < 0x8000:
            a *= 256
        target = (a) * pow(2, 8 * (bits/MM - 3))

        # new target
        new_target = min( max_target, (target * nActualTimespan)/nTargetTimespan )

        # convert it to bits
        c = ("%064X"%new_target)[2:]
        i = 31
        while c[0:2]=="00":
            c = c[2:]
            i -= 1

        c = int('0x'+c[0:6],16)
        if c >= 0x800000:
            c /= 256
            i += 1

        new_bits = c + MM * i
        return new_bits, new_target


Currency = Viacoin

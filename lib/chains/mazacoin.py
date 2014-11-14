'''Chain-specific Mazacoin code'''
from cryptocur import CryptoCur, hash_encode, hash_decode, rev_hex, int_to_hex, sha256, Hash
import os

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

    block_explorers = {
        'Mazacha.in': 'https://mazacha.in/tx/'
    }

    base_units = {
        'MZC': 8
    }

    chunk_size = 2016

    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'thunderfuck.shastafareye.net':{'t':'29956', 's':'29957', 'h':'80', 'g':'443'},
    }

    def set_headers_path(self, path):
        self.headers_path = path

    def path(self):
        return self.headers_path

    def verify_chain(self, chain):

        first_header = chain[0]
        prev_header = self.read_header(first_header.get('block_height') -1)

        for header in chain:

            height = header.get('block_height')

            prev_hash = self.hash_header(prev_header)
            bits, target = self.get_target(height, chain)
            _hash = self.hash_header(header)
            try:
                assert prev_hash == header.get('prev_block_hash')
                assert bits == header.get('bits')
                assert int('0x'+_hash,16) < target
            except Exception:
                return False

            prev_header = header

        return True

    def verify_chunk(self, index, hexdata):
        data = hexdata.decode('hex')
        height = index*self.chunk_size
        num = len(data)/80

        if index == 0:
            previous_hash = ("0"*64)
        else:
            prev_header = self.read_header(index*self.chunk_size-1)
            if prev_header is None: raise
            previous_hash = self.hash_header(prev_header)

#        bits, target = self.get_target(index)

        for i in range(num):
            height = index*self.chunk_size + i
            bits, target = self.get_target(height)
            raw_header = data[i*80:(i+1)*80]
            header = self.header_from_string(raw_header)
            _hash = self.hash_header(header)
            assert previous_hash == header.get('prev_block_hash')
            assert bits == header.get('bits')
            assert int('0x'+_hash,16) < target

            self.save_header(header, height)
            previous_header = header
            previous_hash = _hash

#        self.save_chunk(index, data)
#        print_error("validated chunk %d"%height)

    def header_to_string(self, res):
        s = int_to_hex(res.get('version'),4) \
            + rev_hex(res.get('prev_block_hash')) \
            + rev_hex(res.get('merkle_root')) \
            + int_to_hex(int(res.get('timestamp')),4) \
            + int_to_hex(int(res.get('bits')),4) \
            + int_to_hex(int(res.get('nonce')),4)
        return s


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
        return rev_hex(Hash(self.header_to_string(header).decode('hex')).encode('hex'))

    def save_chunk(self, index, chunk):
        filename = self.path()
        f = open(filename,'rb+')
        f.seek(index*self.chunk_size*80)
        h = f.write(chunk)
        f.close()
#        self.set_local_height()

    def save_header(self, header, height=None):
        data = self.header_to_string(header).decode('hex')
        assert len(data) == 80
        if height is None: height = header.get('block_height')
        filename = self.path()
        f = open(filename,'rb+')
        f.seek(height*80)
        h = f.write(data)
        f.close()
#        self.set_local_height()


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

    def bits_to_target(self, bits):
        MM = 256*256*256
        a = bits%MM
        if a < 0x8000:
            a *= 256
        target = (a) * pow(2, 8 * (bits/MM - 3))
        return target

    def target_to_bits(self, target):
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



    def get_target_v1(self, block_height, chain=None):
        # params
        nTargetTimespan = 8 * 60
        nTargetSpacing = 120
        interval = nTargetTimespan / nTargetSpacing # 4
        nAveragingInterval = interval * 20 # 80
        nAveragingTargetTimespan = nAveragingInterval * nTargetSpacing # 9600
        nMaxAdjustDown = 20
        nMaxAdjustUp = 15
        nMinActualTimespan = nAveragingTargetTimespan * (100 - nMaxAdjustUp) / 100
        nMaxActualTimespan = nAveragingTargetTimespan * (100 + nMaxAdjustDown) / 100


        if chain is None:
            chain = []  # Do not use mutables as default values!

# btc        max_target = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
        max_target = 0x00000FFFF0000000000000000000000000000000000000000000000000000000
        if block_height == 0: return 0x1e0ffff0, max_target

        # Start diff
        start_target = 0x00000003FFFF0000000000000000000000000000000000000000000000000000
        if block_height < nAveragingInterval: return 0x1d03ffff, start_target

        last = self.read_header(block_height-1)
        if last is None:
            for h in chain:
                if h.get('block_height') == block_height-1:
                    last = h


        # Only change on each interval
        if not block_height % interval == 0:
            return self.get_target_v1(block_height-1, chain)


        # first = go back by averagingInterval
        first = self.read_header((block_height-1)-(nAveragingInterval-1))
        if first is None:
            for fh in chain:
                if fh.get('block_height') == (block_height-1)-(nAveragingInterval-1):
                    first = fh


        nActualTimespan = last.get('timestamp') - first.get('timestamp')
        nActualTimespan = max(nActualTimespan, nMinActualTimespan)
        nActualTimespan = min(nActualTimespan, nMaxActualTimespan)

        bits = last.get('bits')
        # convert to bignum
        MM = 256*256*256
        a = bits%MM
        if a < 0x8000:
            a *= 256
        target = (a) * pow(2, 8 * (bits/MM - 3))

        # new target
        new_target = min( max_target, (target * nActualTimespan)/nAveragingTargetTimespan )

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


    def get_target_dgw3(self, block_height, chain=None):
        if chain is None:
            chain = []

        last = self.read_header(block_height-1)
        if last is None:
            for h in chain:
                if h.get('block_height') == block_height-1:
                    last = h

        # params
        BlockLastSolved = last
        BlockReading = last
        BlockCreating = block_height
        nActualTimespan = 0
        LastBlockTime = 0
        PastBlocksMin = 24
        PastBlocksMax = 24
        CountBlocks = 0
        PastDifficultyAverage = 0
        PastDifficultyAveragePrev = 0
        bnNum = 0

        max_target = 0x00000FFFF0000000000000000000000000000000000000000000000000000000

        if BlockLastSolved is None or block_height-1 < PastBlocksMin:
            return 0x1e0ffff0, max_target
        for i in range(1, PastBlocksMax + 1):
            CountBlocks += 1

            if CountBlocks <= PastBlocksMin:
                if CountBlocks == 1:
                    PastDifficultyAverage = self.bits_to_target(BlockReading.get('bits'))
                else:
                    bnNum = self.bits_to_target(BlockReading.get('bits'))
                    PastDifficultyAverage = ((PastDifficultyAveragePrev * CountBlocks)+(bnNum)) / (CountBlocks + 1)
                PastDifficultyAveragePrev = PastDifficultyAverage

            if LastBlockTime > 0:
                Diff = (LastBlockTime - BlockReading.get('timestamp'))
                nActualTimespan += Diff
            LastBlockTime = BlockReading.get('timestamp')

            BlockReading = self.read_header((block_height-1) - CountBlocks)
            if BlockReading is None:
                for br in chain:
                    if br.get('block_height') == (block_height-1) - CountBlocks:
                        BlockReading = br

        bnNew = PastDifficultyAverage
        nTargetTimespan = CountBlocks * 120

        nActualTimespan = max(nActualTimespan, nTargetTimespan/3)
        nActualTimespan = min(nActualTimespan, nTargetTimespan*3)

        # retarget
        bnNew *= nActualTimespan
        bnNew /= nTargetTimespan

        bnNew = min(bnNew, max_target)

        new_bits = self.target_to_bits(bnNew)
        return new_bits, bnNew

    def get_target(self, block_height, chain=None):
        if chain is None:
            chain = []  # Do not use mutables as default values!

        DiffMode = 1
        if block_height >= 100000: DiffMode = 2

        if DiffMode == 1: return self.get_target_v1(block_height, chain)
        elif DiffMode == 2: return self.get_target_dgw3(block_height, chain)

        return self.get_target_dgw3(block_height, chain)


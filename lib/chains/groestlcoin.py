from cryptocur import CryptoCur, hash_encode, hash_decode, rev_hex, int_to_hex, bits_to_target, target_to_bits
import os

import coinhash

class Groestlcoin(CryptoCur):
    PoW = True
    chain_index = 17
    coin_name = 'Groestlcoin'
    code = 'GRS'
    p2pkh_version = 36
    p2sh_version = 5
    wif_version = 128
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 2000000
    RECOMMENDED_FEE = 2000000
    COINBASE_MATURITY = 100

    base58_hash = coinhash.GroestlHash
    header_hash = coinhash.GroestlHash
    transaction_hash = coinhash.SHA256Hash

    block_explorers = {
        'cryptoID.info': 'https://chainz.cryptoid.info/grs/tx.dws?',
        'MultiFaucet.tk': 'http://www.multifaucet.tk/index.php?blockexplorer=GRS&txid='
    }

    chunk_size = 2016

    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'electrum1.groestlcoin.org':DEFAULT_PORTS,
        'electrum2.groestlcoin.org':DEFAULT_PORTS,
    }

    checkpoints = {
        0: "00000ac5927c594d49cc0bdb81759d0da8297eb614683d3acb62f0703b639023",
        111111: "00000000013de206275ee83f93bee57622335e422acbf126a37020484c6e113c",
    }

    def reorg_handler(self, local_height):
        name = self.path()
        if os.path.exists(name):
            f = open(name, 'rb+')
            f.seek( (local_height - 100) *80)
            f.truncate()
            f.close()


    def verify_chain(self, chain):

        first_header = chain[0]
        prev_header = self.read_header(first_header.get('block_height') -1)

        for header in chain:

            height = header.get('block_height')

            prev_hash = self.hash_header(prev_header)
            if height >= 100000:
                bits, target = self.get_target(height, chain)
            _hash = self.hash_header(header)
            try:
                assert prev_hash == header.get('prev_block_hash')
                if height >= 100000:
                    assert bits == header.get('bits')
                    assert int('0x'+_hash,16) < target
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
            _hash = self.hash_header(header)
            assert previous_hash == header.get('prev_block_hash')
            # If using diff retarget, calculate/verify bits
            if self.PoW and height >= 100000:
                bits, target = self.get_target(height)
                assert bits == header.get('bits')
                assert int('0x'+_hash,16) < target
            if self.PoW:
                self.save_header(header, height)

            previous_header = header
            previous_hash = _hash

        if self.PoW == False:
            self.save_chunk(index, data)

    def save_header(self, header, height=None):
        data = self.header_to_string(header).decode('hex')
        assert len(data) == 80
        if height is None: height = header.get('block_height')
        filename = self.path()
        f = open(filename,'rb+')
        f.seek(height*80)
        h = f.write(data)
        f.close()


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
                    PastDifficultyAverage = bits_to_target(BlockReading.get('bits'))
                else:
                    bnNum = bits_to_target(BlockReading.get('bits'))
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
        nTargetTimespan = CountBlocks * 60

        nActualTimespan = max(nActualTimespan, nTargetTimespan/3)
        nActualTimespan = min(nActualTimespan, nTargetTimespan*3)

        # retarget
        bnNew *= nActualTimespan
        bnNew /= nTargetTimespan
        bnNew = min(bnNew, max_target)

        new_bits = target_to_bits(bnNew)
        return new_bits, bnNew

    def get_target(self, block_height, chain=None):
        if chain is None:
            chain = []  # Do not use mutables as default values!

        # DGW3 starts at block 99,999
        assert block_height >= 100000
        return self.get_target_dgw3(block_height, chain)

Currency = Groestlcoin

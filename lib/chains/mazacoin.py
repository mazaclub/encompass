'''Chain-specific Mazacoin code'''
from cryptocur import CryptoCur, hash_encode, hash_decode, rev_hex, int_to_hex, bits_to_target, target_to_bits
import os

from coinhash import SHA256dHash

class Mazacoin(CryptoCur):
    PoW = True
    chain_index = 13
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

    chunk_size = 2016

    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'tate.maza.club':DEFAULT_PORTS,
        'tate1.maza.club':DEFAULT_PORTS,
        'tate2.maza.club':DEFAULT_PORTS,
        'tate.cryptoadhd.com':DEFAULT_PORTS,
    }

    checkpoints = {
        0: "00000c7c73d8ce604178dae13f0fc6ec0be3275614366d44b1b4b5c6e238c60c",
        183600: "0000000000000787f10fa4a547822f8170f1f182ca0de60ecd2de189471da885",
    }

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
        nTargetTimespan = CountBlocks * 120

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

        DiffMode = 1
        if block_height >= 100000: DiffMode = 2

        if DiffMode == 1: return self.get_target_v1(block_height, chain)
        elif DiffMode == 2: return self.get_target_dgw3(block_height, chain)

        return self.get_target_dgw3(block_height, chain)

Currency = Mazacoin

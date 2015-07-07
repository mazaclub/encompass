'''Chain-specific Blackcoin code'''
from cryptocur import CryptoCur, hash_encode, hash_decode, rev_hex, int_to_hex, chainhook
import os
import time

from coinhash import SHA256dHash, ScryptHash

class Blackcoin(CryptoCur):
    PoW = False
    chain_index = 10
    coin_name = 'Blackcoin'
    code = 'BLK'
    p2pkh_version = 25
    p2sh_version = 85
    wif_version = 153
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 10000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 500

    block_explorers = {
        'Coinplorer.com': 'https://coinplorer.com/BC/Transactions/',
        'Bchain.info': 'https://bchain.info/BC/tx/'
    }

    chunk_size = 2016

    # Network
    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'blk-cce-1.coinomi.net':{'t':'5015','s':'5015','h':'8081','g':'8082'},
        'blk-cce-2.coinomi.net':{'t':'5015','s':'5015','h':'8081','g':'8082'}
    }

    checkpoints = {
        0: "000001faef25dec4fbcf906e6242621df2c183bf232f263d0ba5b101911e4563",
        319002: "0011494d03b2cdf1ecfc8b0818f1e0ef7ee1d9e9b3d1279c10d35456bc3899ef",
    }

    def hash_header(self, header):
        if header.get('version', 0) > 6:
            return rev_hex(SHA256dHash(self.header_to_string(header).decode('hex')).encode('hex'))
        else:
            return rev_hex(ScryptHash(self.header_to_string(header).decode('hex')).encode('hex'))

    def get_target(self, index, chain=None):
        if chain is None:
            chain = []  # Do not use mutables as default values!

        max_target = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
        if index == 0: return 0x1d00ffff, max_target

        first = self.read_header((index-1)*2016)
        last = self.read_header(index*2016-1)
        if last is None:
            for h in chain:
                if h.get('block_height') == index*2016-1:
                    last = h

        nActualTimespan = last.get('timestamp') - first.get('timestamp')
        nTargetTimespan = 14*24*60*60
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

    @chainhook
    def transaction_deserialize_tx_fields(self, vds, fields):
        timestamp = ('timestamp', vds.read_int32, True)
        fields.insert(1, timestamp)

    @chainhook
    def transaction_serialize(self, tx, for_sig, fields):
        unix_time = getattr(tx, 'timestamp', None)
        if unix_time is None:
            unix_time = int(time.time())
        timestamp = ('timestamp', [int_to_hex(unix_time, 4)])
        fields.insert(1, timestamp)

Currency = Blackcoin

'''Chain-specific Peercoin code'''
from cryptocur import CryptoCur, hash_encode, hash_decode, rev_hex, int_to_hex, chainhook
import os
import time

class Peercoin(CryptoCur):
    PoW = False
    chain_index = 6
    coin_name = 'Peercoin'
    code = 'PPC'
    p2pkh_version = 55
    p2sh_version = 117
    wif_version = 128
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 10000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 500

    block_explorers = {
        'PeercoinExplorer.info': 'https://peercoinexplorer.info/tx/'
    }

    base_units = {
        'HPPC': 8,
        'PPC': 6,
        'mPPC': 3
    }

    chunk_size = 2016

    # Network
    DEFAULT_PORTS = {'t':'5004', 's':'5004', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'ppc-cce-1.coinomi.net':DEFAULT_PORTS
    }

    checkpoints = {
        0: "0000000032fe677166d54963b62a4677d8957e87c508eaa4fd7eb1c880cd27e3",
        99999: "27fd5e1de16a4270eb8c68dee2754a64da6312c7c3a0e99a7e6776246be1ee3f",
    }

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

Currency = Peercoin

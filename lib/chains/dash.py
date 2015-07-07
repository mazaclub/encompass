'''Chain-specific Dash code'''
from cryptocur import CryptoCur, hash_encode, hash_decode, rev_hex, int_to_hex
import os

import coinhash

class Dash(CryptoCur):
    PoW = False
    chain_index = 5
    coin_name = 'Dash'
    code = 'DASH'
    p2pkh_version = 76
    p2sh_version = 16
    wif_version = 204
    ext_pub_version = '02fe52f8'
    ext_priv_version = '02fe52cc'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 1000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 100

    header_hash = coinhash.X11Hash

    block_explorers = {
        'CryptoID': 'https://chainz.cryptoid.info/dash/',
        'CoinPlorer': 'https://coinplorer.com/DRK',
    }

    base_units = {
        'DASH': 8,
        'mDASH': 5,
        'uDASH': 2,
    }

    chunk_size = 2016

    # Network
    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'electrum.darkcointalk.org':DEFAULT_PORTS, # propulsion
        'drk1.electrum-servers.us':DEFAULT_PORTS,  # elm4ever
        'electrum.drk.siampm.com':DEFAULT_PORTS,   # thelazier
        'electrum-drk.club':DEFAULT_PORTS,         # duffman
    }

    checkpoints = {
        0: "00000ffd590b1485b3caadc19b22e6379c733355108f107a430458cdf3407ab6",
        217752: "00000000000a7baeb2148272a7e14edf5af99a64af456c0afc23d15a0918b704",
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
        nTargetTimespan = 24*60*60
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

Currency = Dash

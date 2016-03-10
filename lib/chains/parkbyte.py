'''Chain-specific ParkByte code'''
from cryptocur import CryptoCur, hash_encode, hash_decode, rev_hex, int_to_hex, chainhook
import os
import time

class ParkByte(CryptoCur):
    PoW = False
    chain_index = 36
    coin_name = 'ParkByte'
    code = 'PKB'
    p2pkh_version = 55
    p2sh_version = 28
    wif_version = 183
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 1000
    RECOMMENDED_FEE = 2000
    COINBASE_MATURITY = 120

    # ParkByte timestamp fix
    unix_time = int(time.time())

    block_explorers = {
        'CryptoID.info': 'https://chainz.cryptoid.info/pkb/tx.dws?'
    }

    base_units = {
        'PKB': 8
    }

    chunk_size = 2016

    # Network
    DEFAULT_PORTS = {'t':'5035', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'electrum.uk1.parkbyte.com':DEFAULT_PORTS,
        'electrum.eu1.parkbyte.com':DEFAULT_PORTS,
        'electrum.eu2.parkbyte.com':DEFAULT_PORTS,
        'electrum.canada.parkbyte.com':DEFAULT_PORTS
    }

    checkpoints = {
        0: "000000a49664091ce50794d84fb243cde97738534b554b2022fa00a029d0ab7c",
        300000: " 15bc49fb520cfe5d80a2a3e08f13658862ba1641b27c521159e64b77dea949ed"
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
        # ParkByte mod - when spending multiple inputs, timestamp must be the same for all inputs or RPC will reject TX
        if (int(time.time()) - self.unix_time) >= 10:
            self.unix_time = int(time.time())
        timestamp = ('timestamp', [int_to_hex(self.unix_time, 4)])
        fields.insert(1, timestamp)

Currency = ParkByte
'''Chain-specific Clam code'''
from cryptocur import CryptoCur, hash_encode, hash_decode, rev_hex, int_to_hex, var_int, chainhook
import os
import time

from coinhash import SHA256dHash

TX_VERSION_CLAMSPEECH = 2

class Clam(CryptoCur):
    PoW = False
    chain_index = 23
    coin_name = 'Clam'
    code = 'CLAMS'
    p2pkh_version = 137
    p2sh_version = 13
    wif_version = 133
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 10000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 500

    block_explorers = {
        'Clamsight.com': 'https://clamsight.com/tx/'
    }

    base_units = {
        'CLAMS': 8
    }

    chunk_size = 2016

    # Network
    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'scallop.us-west-2.maza.club':DEFAULT_PORTS
    }

    def verify_chain(self, chain):

        first_header = chain[0]
        prev_header = self.read_header(first_header.get('block_height') -1)

        if not self.PoW:
            return True

        for header in chain:

            height = header.get('block_height')

            prev_hash = self.hash_header(prev_header)
            bits, target = self.get_target(height/2016, chain)
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
        height = index*2016
        num = len(data)/80

        if not self.PoW:
            self.save_chunk(index, data)
            return

        if index == 0:
            previous_hash = ("0"*64)
        else:
            prev_header = self.read_header(index*2016-1)
            if prev_header is None: raise
            previous_hash = self.hash_header(prev_header)

        bits, target = self.get_target(index)

        for i in range(num):
            height = index*2016 + i
            raw_header = data[i*80:(i+1)*80]
            header = self.header_from_string(raw_header)
            _hash = self.hash_header(header)
            assert previous_hash == header.get('prev_block_hash')
            assert bits == header.get('bits')
            assert int('0x'+_hash,16) < target

            previous_header = header
            previous_hash = _hash

        self.save_chunk(index, data)

    def hash_header(self, header):
        return rev_hex(SHA256dHash(self.header_to_string(header).decode('hex')).encode('hex'))

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
        timestamp = ('timestamp', vds.read_int32, False)
        fields.insert(1, timestamp)
        clamspeech = ('clamspeech', 'read_bytes_compact_size', True)
        fields.append(clamspeech)

    @chainhook
    def transaction_serialize(self, tx, for_sig, fields):
        unix_time = getattr(tx, 'timestamp', None)
        if unix_time is None:
            unix_time = int(time.time())
        timestamp = ('timestamp', int_to_hex(unix_time, 4))
        fields.insert(1, timestamp)

        tx_version = getattr(tx, 'version', 1)
        if tx_version < TX_VERSION_CLAMSPEECH:
            return
        else:
            txver = ('version', int_to_hex(tx_version, 4))
            fields[0] = txver

        speech = ('clamspeech', getattr(tx, 'clamspeech', '').encode('hex'))
        speech_len = ('clamspeech_len', var_int(len(speech[1])/2))
        fields.insert(-1,  speech_len)
        fields.insert(-1,  speech)

Currency = Clam

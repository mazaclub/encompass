'''Chain-specific Feathercoin code'''
from cryptocur import CryptoCur, hash_encode, hash_decode, rev_hex, int_to_hex, sha256, Hash
import os

import neoscrypt
import ltc_scrypt

HashNeoscrypt = lambda x: neoscrypt.getPoWHash(x)
HashScrypt = lambda x: ltc_scrypt.getPoWHash(x)

class Feathercoin(CryptoCur):
    PoW = False
    chain_index = 8
    coin_name = 'Feathercoin'
    code = 'FTC'
    p2pkh_version = 14
    p2sh_version = 5
    wif_version = 142

    block_explorers = {
        'Bchain.info': 'https://bchain.info/FTC/tx/',
        'Ftc-c.com': 'http://block.ftc-c.com/tx/'
    }

    base_units = {
        'FTC': 8,
        'mFTC': 5
    }


    DEFAULT_PORTS = {'t':'5017', 's':'5017', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'ftc-cce-1.coinomi.net':DEFAULT_PORTS,
        'ftc-cce-2.coinomi.net':DEFAULT_PORTS
    }

    def verify_chain(self, chain):

        # for now, assume true
        return True

        first_header = chain[0]
        prev_header = self.read_header(first_header.get('block_height') -1)

        for header in chain:

            height = header.get('block_height')

            prev_hash = self.hash_header(prev_header)
            bits, target = self.get_target(height/2016, chain)
            _hash = self.pow_hash_header(header)
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

        # for now, assume true
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
            _hash = self.pow_hash_header(header)
            assert previous_hash == header.get('prev_block_hash')
            assert bits == header.get('bits')
            assert int('0x'+_hash,16) < target

            previous_header = header
            previous_hash = self.hash_header(header)

        self.save_chunk(index, data)

    def hash_header(self, header):
        return rev_hex(Hash(self.header_to_string(header).decode('hex')).encode('hex'))

    def pow_hash_header(self, header):
        # TODO
        return rev_hex(getPoWHash(self.header_to_string(header).decode('hex')).encode('hex'))

    def get_target(self, index, chain=[]):

        max_target = 0x00000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        if index == 0: return 0x1e0ffff0, 0x00000FFFF0000000000000000000000000000000000000000000000000000000

        # Litecoin: go back the full period unless it's the first retarget
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

Currency = Feathercoin

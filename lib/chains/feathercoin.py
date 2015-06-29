'''Chain-specific Feathercoin code'''
from cryptocur import CryptoCur, hash_encode, hash_decode, rev_hex, int_to_hex, bits_to_target, target_to_bits
import os

from coinhash import SHA256dHash, NeoscryptHash, ScryptHash

switch_v2_time = 1413936000
fork_one = 33000
fork_two = 87948
fork_three = 204639
fork_four = 432000

class Feathercoin(CryptoCur):
    PoW = True
    chain_index = 8
    coin_name = 'Feathercoin'
    code = 'FTC'
    p2pkh_version = 14
    p2sh_version = 5
    wif_version = 142

    MIN_RELAY_TX_FEE = 2000000
    RECOMMENDED_FEE = 2000000

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

    def save_header(self, header, height=None):
        data = self.header_to_string(header).decode('hex')
        assert len(data) == 80
        if height is None: height = header.get('block_height')
        filename = self.path()
        f = open(filename,'rb+')
        f.seek(height*80)
        h = f.write(data)
        f.close()

    def verify_chain(self, chain):
        first_header = chain[0]
        prev_header = self.read_header(first_header.get('block_height') -1)

        if not self.PoW:
            for header in chain:
                prev_hash = self.hash_header(prev_header)
                try:
                    assert prev_hash == header.get('prev_block_hash')
                except Exception:
                    return False
                prev_header = header
            return True

        for header in chain:

            height = header.get('block_height')

            prev_hash = self.hash_header(prev_header)
            bits, target = self.get_target(height, chain)
            _hash = self.pow_hash_header(header, height)
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

        if index == 0:  
            previous_hash = ("0"*64)
        else:
            prev_header = self.read_header(index*2016-1)
            if prev_header is None: raise
            previous_hash = self.hash_header(prev_header)


        if not self.PoW:
            for i in range(num):
                raw_header = data[i*80:(i+1)*80]
                header = self.header_from_string(raw_header)
                assert previous_hash == header.get('prev_block_hash')
                previous_header = header
                previous_hash = self.hash_header(header)
            self.save_chunk(index, data)
            return

        for i in range(num):
            height = index*2016 + i
            raw_header = data[i*80:(i+1)*80]
            header = self.header_from_string(raw_header)
            bits, target = self.get_target(height)
            _hash = self.pow_hash_header(header, height)
            assert previous_hash == header.get('prev_block_hash')
            assert bits == header.get('bits')
            assert int('0x'+_hash,16) < target

            self.save_header(header, height)
            previous_header = header
            previous_hash = self.hash_header(header)

#        self.save_chunk(index, data)

    def hash_header(self, header):
        return rev_hex(SHA256dHash(self.header_to_string(header).decode('hex')).encode('hex'))

    def pow_hash_header(self, header, height):
        # TODO
        HASH_SCRYPT = 1
        HASH_NEOSCRYPT = 2
        HASH_ALGO = HASH_NEOSCRYPT
        if header.get('timestamp') < switch_v2_time:
            HASH_ALGO = HASH_SCRYPT
        else:
            if height < fork_four:
                HASH_ALGO = HASH_SCRYPT

        if HASH_ALGO == HASH_SCRYPT:
            return rev_hex(ScryptHash(self.header_to_string(header).decode('hex')).encode('hex'))
        else:
            return rev_hex(NeoscryptHash(self.header_to_string(header).decode('hex')).encode('hex'))

    def get_target(self, height, chain=None):
        if chain is None:
            chain = []

        max_target = 0x00000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        if height == 0: return 0x1e0ffff0, max_target

        neoscrypt_target = 0x0000003FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        neoscrypt_bits = 0x1d3fffff

        target_timespan = 3.5 * 24 * 60 * 60 # 3.5 days
        target_spacing = 2.5 * 60 # 2.5 minutes

        if height == fork_four:
            return neoscrypt_bits, neoscrypt_target

        if height >= fork_one:
            target_timespan = (7 * 24 * 60 * 60) / 8 # 7/8 days
        if height >= fork_two:
            target_timespan = (7 * 24 * 60 * 60) / 32 # 7/32 days
        if height >= fork_three:
            target_timespan = 60 # 1 minute timespan
            target_spacing = 60 # 1 minute block

        # 2016 initially, 504 after 1st fork, 126 after 2nd fork, 15 after 3rd fork
        interval = target_timespan/target_spacing

        is_hard_fork = height == fork_one or height == fork_two or height == fork_three or height == fork_four

        last = self.read_header(height - 1)
        if last is None:
            for h in chain:
                if h.get('block_height') == height - 1:
                    last = h

        # difficulty rules regular blocks
        if (height % interval != 0) and (not is_hard_fork) and height < fork_three:
            return last.get('bits'), bits_to_target(last.get('bits'))

        # first retarget after genesis
        if interval >= height:
            interval = height - 1

        # go back by interval
        first = self.read_header((height-1) - interval)
        if first is None:
            for h in chain:
                if h.get('block_height') == (height-1) - interval:
                    first = h

        actual_timespan = last.get('timestamp') - first.get('timestamp')
        # additional leveraging over 4x interval window
        if height >= fork_two and height < fork_three:
            interval *= 4
            first = self.read_header((height-1) - interval)
            if first is None:
                for h in chain:
                    if h.get('block_height') == (height-1) - interval:
                        first = h

            actual_timespan_long = (last.get('timestamp') - first.get('timestamp')) / 4

            # average between short and long windows
            actual_timespan_avg = (actual_timespan + actual_timespan_long) / 2

            # apply .25 damping
            actual_timespan = actual_timespan_avg + 3*target_timespan
            actual_timespan /= 4

        # additional leveraging over 15, 120 and 480 block window
        if height >= fork_three:
            interval *= 480

            first_short = self.read_header((height-1) - 15)
            if first_short is None:
                for h in chain:
                    if h.get('block_height') == (height-1) - 15: first_short = h
            first_short_time = first_short.get('timestamp')

            first_medium = self.read_header((height-1) - 120)
            if first_medium is None:
                for h in chain:
                    if h.get('block_height') == (height-1) - 120: first_medium = h
            first_medium_time = first_medium.get('timestamp')

            first_long = self.read_header((height-1) - interval)
            if first_long is None:
                for h in chain:
                    if h.get('block_height') == (height-1) - interval: first_long = h

            actual_timespan_short = (last.get('timestamp') - first_short_time) / 15
            actual_timespan_medium = (last.get('timestamp') - first_medium_time) / 120
            actual_timespan_long = (last.get('timestamp') - first_long.get('timestamp')) / 480

            actual_timespan_avg = (actual_timespan_short + actual_timespan_medium + actual_timespan_long) / 3

            # apply .25 damping
            actual_timespan = actual_timespan_avg + 3*target_timespan
            actual_timespan /= 4

        # initial settings (4.0 difficulty limiter)
        actual_timespan_max = target_timespan * 4
        actual_timespan_min = target_timespan / 4

        # 1st hard fork
        if height >= fork_one:
            actual_timespan_max = target_timespan*99/70
            actual_timespan_min = target_timespan*70/99

        # 2nd hard fork
        if height >= fork_two:
            actual_timespan_max = target_timespan*494/453
            actual_timespan_min = target_timespan*453/494

        actual_timespan = max(actual_timespan, actual_timespan_min)
        actual_timespan = min(actual_timespan, actual_timespan_max)

        # retarget
        new_diff = bits_to_target(last.get('bits'))
        new_diff *= actual_timespan
        new_diff /= target_timespan

        new_diff = min(new_diff, max_target)
        return target_to_bits(new_diff), new_diff


Currency = Feathercoin

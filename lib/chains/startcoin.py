"""Chain-specific StartCOIN code."""
from cryptocur import CryptoCur, bits_to_target, target_to_bits

import coinhash

height_rolloff = 120 # minimum diff blocks
max_target = 0x00000FFFF0000000000000000000000000000000000000000000000000000000
target_timespan = 60 # StartCOIN: 1 minute
target_spacing = 60 # 1 minute
interval = target_timespan / target_spacing # 1

class StartCOIN(CryptoCur):
    PoW = True
    chain_index = 999
    coin_name = 'StartCOIN'
    code = 'START'
    p2pkh_version = 125
    p2sh_version = 5
    wif_version = 253

    DUST_THRESHOLD = 0
    MIN_RELAY_TX_FEE = 100000
    RECOMMENDED_FEE = 100000
    COINBASE_MATURITY = 100

    header_hash = coinhash.X11Hash

    block_explorers = {
        'startcoin.org': 'https://explorer.startcoin.org/tx/'
    }

    chunk_size = 2016

    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'localhost':DEFAULT_PORTS # TODO
    }

    def get_target_digishield(self, height, chain):
        if height < height_rolloff:
            raise Exception('Digishield is not active at this height.')

        last = self.read_header(height - 1)
        if last is None:
            for h in chain:
                if h.get('block_height') == height - 1:
                    last = h

        if last is None:
            raise Exception("There is no last block for %d." % height)

        # err this shouldn't happen since interval is 1
        if height % interval != 0:
            return last.get('bits'), bits_to_target(last.get('bits'))

        blocks_to_go_back = interval - 1
        if height != interval:
            blocks_to_go_back = interval

        last_height = height - 1
        first = self.read_header(last_height - blocks_to_go_back)

        actual_timespan = last.get('timestamp') - first.get('timestamp')
        actual_timespan = target_timespan + (actual_timespan - target_timespan) / 8

        # digishield
        actual_timespan = max(actual_timespan, target_timespan - (target_timespan/4))
        actual_timespan = min(actual_timespan, target_timespan + (target_timespan/2))

        # retarget
        bnNew = bits_to_target(last.get('bits'))
        bnNew *= actual_timespan
        bnNew /= target_timespan

        bnNew = min(bnNew, max_target)

        return target_to_bits(bnNew), bnNew

    def get_target(self, height, chain=None):
        if chain is None: chain = []

        if height < height_rolloff:
            return bits_to_target(max_target), max_target
        return self.get_target_digishield(height, chain)

Currency = StartCOIN

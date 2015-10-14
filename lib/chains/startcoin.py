"""Chain-specific StartCOIN code."""
from cryptocur import CryptoCur, bits_to_target, target_to_bits

import coinhash

height_rolloff = 120 # minimum diff blocks
max_target = 0x00000FFFF0000000000000000000000000000000000000000000000000000000
target_timespan = 60 # StartCOIN: 1 minute
target_spacing = 60 # 1 minute
interval = target_timespan / target_spacing # 1

class StartCOIN(CryptoCur):
    PoW = False
    chain_index = 38
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
        'start.electrum.maza.club':{'t':'50151', 's':'50152', 'h':'8081', 'g':'8082'},
        'start.mercury.maza.club':{'t':'50051', 's':'50052', 'h':'8081', 'g':'8082'},
    }


Currency = StartCOIN

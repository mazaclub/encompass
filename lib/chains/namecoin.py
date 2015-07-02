"""Chain-specific Namecoin code."""

from cryptocur import CryptoCur, hash_encode, hash_decode, rev_hex, int_to_hex

from coinhash import SHA256dHash

class Namecoin(CryptoCur):
    PoW = False
    chain_index = 7
    coin_name = 'Namecoin'
    code = 'NMC'
    p2pkh_version = 52
    p2sh_version = 13
    wif_version = 180
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 100000
    RECOMMENDED_FEE = 500000
    COINBASE_MATURITY = 100

    block_explorers = {
        'Namecoin.info': 'https://explorer.namecoin.info/tx/',
        'Namecha.in': 'https://namecha.in/tx/',
        'Coinplorer.com': 'https://coinplorer.com/NMC/Transactions/'
    }

    base_units = {
        'NMC': 8
    }

    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'e-nmc.us-west-2.maza.club': DEFAULT_PORTS,
    }

    def verify_chain(self, chain):
        first_header = chain[0]
        prev_header = self.read_header(first_header.get('block_height') - 1)

        if not self.PoW:
            for header in chain:
                height = header.get('block_height')

                prev_hash = self.hash_header(prev_header)
                _hash = self.hash_header(header)
                try:
                    assert prev_hash == header.get('prev_block_hash')
                except Exception:
                    return False

                prev_header = header
            return True

    def verify_chunk(self, index, hexdata):
        data = hexdata.decode('hex')
        height = index*self.chunk_size
        num = len(data)/80

        if index == 0:
            previous_hash = ("0"*64)
        else:
            prev_header = self.read_header(index*self.chunk_size-1)
            if prev_header is None: raise
            previous_hash = self.hash_header(prev_header)

        if not self.PoW:
            for i in range(num):
                height = index*self.chunk_size + i
                raw_header = data[i*80:(i+1)*80]
                header = self.header_from_string(raw_header)
                _hash = self.hash_header(header)
                assert previous_hash == header.get('prev_block_hash')

                previous_header = header
                previous_hash = _hash

            self.save_chunk(index, data)

    def hash_header(self, header):
        return rev_hex(SHA256dHash(self.header_to_string(header).decode('hex')).encode('hex'))


Currency = Namecoin

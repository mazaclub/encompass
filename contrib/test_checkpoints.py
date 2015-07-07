"""Test checkpoints of all chains.

Requires that headers be synchronized on the machine running this,
and that the code being tested is installed."""
import os

import chainkey
from chainkey import chainparams
from chainkey.util import user_dir

basepath = os.path.join(user_dir(), 'blockchain_headers_')

def test_checkpoints(chain):
    """Test all of chain's checkpoints.

    Returns:
        is_ok, (failed_checkpoint_height, checkpoint_hash, stored_data_hash)
    """
    filename = ''.join([ basepath, chain.code.lower() ])
    chain.set_headers_path(filename)
    for height, block_hash in chain.checkpoints.items():
        stored_header = chain.read_header(height)
        if not stored_header:
            print("  [{}] Skipping block I don't have data for: {}".format(chain.code, height))
            continue
        stored_data_hash = chain.hash_header(stored_header)
        if block_hash != stored_data_hash:
            return False, (height, block_hash, stored_data_hash)
    return True, None

if __name__ == '__main__':
    for c in chainparams.known_chain_codes:
        chain = chainparams.get_chain_instance(c)
        is_ok, fail_data = test_checkpoints(chain)
        if not is_ok:
            print('{} FAILED: Checkpoint at height {} does not match data!'.format(c, fail_data[0]))
            print(' Checkpoint hash : {}\n Stored data hash: {}'.format(fail_data[1], fail_data[2]))
        else:
            print('{} passed.'.format(c))

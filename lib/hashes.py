"""Hash algorithms."""

import coinhash

# Algorithms
#
# base58: Used in address encoding and Base58Check encoding.
# merkle: Used in hashing merkle trees.
# transaction: Used to hash transactions.
hash_algos = {
    'base58': coinhash.SHA256dHash,
    'merkle': coinhash.SHA256dHash,
    'transaction': coinhash.SHA256dHash,
}

def set_hash_algo(name, hash_algo):
    """Generic function for setting an algorithm.

    Specific functions should be used whenever possible.
    This is just for extensibility.
    """
    global hash_algos
    hash_algos[name] = hash_algo

def set_base58_hash(hash_algo):
    """Set the global hash algorithm used in base58 encoding."""
    global hash_algos
    hash_algos['base58'] = hash_algo

def set_transaction_hash(hash_algo):
    """Set the global hash algorithm used in transaction hashing."""
    global hash_algos
    hash_algos['transaction'] = hash_algo

def set_merkle_hash(hash_algo):
    """Set the global hash algorithm used in merkle tree hashing."""
    global hash_algos
    hash_algos['merkle'] = hash_algo

def do_hash(algo, x):
    """Convert the algo from a class method to a coinhash function."""
    algo = getattr(coinhash, algo.__name__)
    return algo(x)



def base58_hash(x):
    return do_hash(hash_algos['base58'], x)

def merkle_hash(x):
    return do_hash(hash_algos['merkle'], x)

def transaction_hash(x):
    return do_hash(hash_algos['transaction'], x)

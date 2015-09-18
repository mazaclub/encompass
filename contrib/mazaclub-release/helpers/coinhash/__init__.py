import hashlib
import neoscrypt
import skeinhash
import qubit_hash
import groestlcoin_hash
import darkcoin_hash
import ltc_scrypt

def SHA256Hash(x):
    """Equivalent to hashlib.sha256(x).digest()."""
    return hashlib.sha256(x).digest()

def SHA256dHash(x):
    """Two rounds of SHA256."""
    return hashlib.sha256(hashlib.sha256(x).digest()).digest()

def NeoscryptHash(x):
    return neoscrypt.getPoWHash(x)

def SkeinHash(x):
    return skeinhash.getPoWHash(x)

def QubitHash(x):
    return qubit_hash.getPoWHash(x)

def GroestlHash(x):
    return groestlcoin_hash.getHash(x, len(x))

def X11Hash(x):
    return darkcoin_hash.getPoWHash(x)

def ScryptHash(x):
    """Scrypt (Litecoin parameters) hash."""
    return ltc_scrypt.getPoWHash(x)

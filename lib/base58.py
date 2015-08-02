import hashlib
import re

from hashes import base58_hash
from util_coin import sha256

############ functions from pywallet #####################

def hash_160(public_key):
    try:
        md = hashlib.new('ripemd160')
        md.update(sha256(public_key))
        return md.digest()
    except Exception:
        import ripemd
        md = ripemd.new(sha256(public_key))
        return md.digest()


def public_key_to_bc_address(public_key, addrtype=0):
    h160 = hash_160(public_key)
    return hash_160_to_bc_address(h160, addrtype)

def hash_160_to_bc_address(h160, addrtype = 0):
    vh160 = chr(addrtype) + h160
    h = base58_hash(vh160)
    addr = vh160 + h[0:4]
    return b58encode(addr)

def bc_address_to_hash_160(addr):
    bytes = b58decode(addr, 25)
    return ord(bytes[0]), bytes[1:21]


__b58chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
__b58base = len(__b58chars)

def b58encode(v):
    """ encode v, which is a string of bytes, to base58."""

    long_value = 0L
    for (i, c) in enumerate(v[::-1]):
        long_value += (256**i) * ord(c)

    result = ''
    while long_value >= __b58base:
        div, mod = divmod(long_value, __b58base)
        result = __b58chars[mod] + result
        long_value = div
    result = __b58chars[long_value] + result

    # Bitcoin does a little leading-zero-compression:
    # leading 0-bytes in the input become leading-1s
    nPad = 0
    for c in v:
        if c == '\0': nPad += 1
        else: break

    return (__b58chars[0]*nPad) + result


def b58decode(v, length):
    """ decode v into a string of len bytes."""
    long_value = 0L
    for (i, c) in enumerate(v[::-1]):
        long_value += __b58chars.find(c) * (__b58base**i)

    result = ''
    while long_value >= 256:
        div, mod = divmod(long_value, 256)
        result = chr(mod) + result
        long_value = div
    result = chr(long_value) + result

    nPad = 0
    for c in v:
        if c == __b58chars[0]: nPad += 1
        else: break

    result = chr(0)*nPad + result
    if length is not None and len(result) != length:
        return None

    return result

def EncodeBase58Check(vchIn):
    """Encodes a string of bytes in Base58 encoding with a checksum."""
    hash = base58_hash(vchIn)
    return b58encode(vchIn + hash[0:4])


def DecodeBase58Check(psz):
    """Decodes a Base58-encoded string and verifies its checksum."""
    vchRet = b58decode(psz, None)
    key = vchRet[0:-4]
    csum = vchRet[-4:]
    hash = base58_hash(key)
    cs32 = hash[0:4]
    if cs32 != csum:
        return None
    else:
        return key

def SecretToASecret(secret, compressed=False, addrtype=128):
    """Converts private key bytes to WIF.

    Args:
        secret (str): Private key bytes.
        compressed (bool): Whether to attach the 'compressed' flag to the encoded WIF key.
        addrtype (int): Blockchain-specific base58 version byte for private keys in WIF.

    Returns:
        WIF key (base58-encoded).

    """
    vchIn = chr(addrtype) + secret
    if compressed: vchIn += '\01'
    return EncodeBase58Check(vchIn)

def ASecretToSecret(key, addrtype=128):
    """Converts a WIF key to private key bytes.

    Args:
        key (str): WIF key (base58-encoded).
        addrtype (int): Blockchain-specific base58 version byte for private keys in WIF.

    Returns:
        String of private key bytes.

    """
    vch = DecodeBase58Check(key)
    if vch and vch[0] == chr(addrtype):
        return vch[1:]
    else:
        return False


def is_compressed(sec, addrtype=128):
    """Returns whether a WIF private key represents a compressed key."""
    b = ASecretToSecret(sec, addrtype)
    return len(b) == 33


def is_valid(addr, active_chain=None):
    return is_address(addr, active_chain)


def is_address(addr, active_chain=None):
    """Determines whether addr is a valid address.

    Args:
        active_chain (CryptoCur): The chain that addr should be valid for.
            Specifying this makes the function more strict. Not only must addr
            be in a valid format, but it must have one of this chain's address versions.
    """
    ADDRESS_RE = re.compile('[1-9A-HJ-NP-Za-km-z]{26,}\\Z')
    if not ADDRESS_RE.match(addr): return False
    try:
        addrtype, h = bc_address_to_hash_160(addr)
    except Exception:
        return False
    # optionally test if it's the right chain
    if active_chain is not None:
        if addrtype != active_chain.p2pkh_version and addrtype != active_chain.p2sh_version:
            return False

    return addr == hash_160_to_bc_address(h, addrtype)


def is_private_key(key, addrtype=128):
    """Returns whether a WIF private key is valid."""
    try:
        k = ASecretToSecret(key, addrtype)
        return k is not False
    except:
        return False



########### end pywallet functions #######################


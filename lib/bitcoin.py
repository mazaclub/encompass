# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2011 thomasv@gitorious
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import hashlib
import sys
import hmac

import version
from util import print_error
import util_coin
import base58

try:
    import ecdsa
except ImportError:
    sys.exit("Error: python-ecdsa does not seem to be installed. Try 'sudo pip install ecdsa'")

from ecdsa.curves import SECP256k1
from ecdsa.ecdsa import generator_secp256k1

import eckey
from eckey import EC_KEY, ser_to_point, GetPubKey, GetPrivKey

################################## transactions

DUST_THRESHOLD = 5430
MIN_RELAY_TX_FEE = 1000
RECOMMENDED_FEE = 50000
COINBASE_MATURITY = 100

# checks if multisig M of N scripts would be standard according to <= Bitcoin 0.9 rules
def is_standard_mofn(m, n):
    if m * 73 + n * 34 <= 496:
        return True
    return False

def get_max_n(m):
    if m < 1 or m > 4: return None
    n = 12
    while not is_standard_mofn(m, n):
        n -= 1
    return n


def rev_hex(s):
    """Deprecated."""
    return util_coin.rev_hex(s)

def int_to_hex(i, length=1):
    """Deprecated."""
    return util_coin.int_to_hex(i, length)

def op_push(i):
    """Deprecated."""
    return util_coin.op_push(i)

def sha256(x):
    """Deprecated."""
    return util_coin.sha256(x)

def Hash(x):
    """Deprecated."""
    return util_coin.Hash(x)

def hash_encode(x):
    """Deprecated."""
    return util_coin.hash_encode(x)

def hash_decode(x):
    """Deprecated."""
    return util_coin.hash_decode(x)

hmac_sha_512 = lambda x,y: hmac.new(x, y, hashlib.sha512).digest()

def is_new_seed(x, prefix=version.SEED_BIP44):
    import mnemonic
    x = mnemonic.prepare_seed(x)
    s = hmac_sha_512("Seed version", x.encode('utf8')).encode('hex')
    return s.startswith(prefix)


def is_old_seed(seed):
    import old_mnemonic
    words = seed.strip().split()
    try:
        old_mnemonic.mn_decode(words)
        uses_electrum_words = True
    except Exception:
        uses_electrum_words = False

    try:
        seed.decode('hex')
        is_hex = (len(seed) == 32)
    except Exception:
        is_hex = False

    return is_hex or (uses_electrum_words and len(words) == 12)


############ functions from pywallet #####################

def hash_160(public_key):
    """Deprecated."""
    return base58.hash_160(public_key)

def public_key_to_bc_address(public_key, addrtype=0):
    """Deprecated."""
    return base58.public_key_to_bc_address(public_key, addrtype)

def hash_160_to_bc_address(h160, addrtype = 0):
    """Deprecated."""
    return base58.hash_160_to_bc_address(h160, addrtype)

def bc_address_to_hash_160(addr):
    """Deprecated."""
    return base58.bc_address_to_hash_160(addr)

def b58encode(v):
    """Deprecated."""
    return base58.b58encode(v)

def b58decode(v, length):
    """Deprecated."""
    return base58.b58decode(v)

def EncodeBase58Check(vchIn):
    """Deprecated."""
    return base58.EncodeBase58Check(vchIn)

def DecodeBase58Check(psz):
    """Deprecated."""
    return base58.DecodeBase58Check(psz)

def SecretToASecret(secret, compressed=False, addrtype=128):
    """Deprecated."""
    return base58.SecretToASecret(secret, compressed, addrtype)

def ASecretToSecret(key, addrtype=128):
    """Deprecated."""
    return base58.ASecretToSecret(key, addrtype)

def regenerate_key(sec, addrtype=128):
    """Deprecated."""
    return eckey.regenerate_key(sec, addrtype)

def is_compressed(sec, addrtype=128):
    """Deprecated."""
    return base58.is_compressed(sec, addrtype)

def public_key_from_private_key(sec, addrtype=128):
    """Deprecated."""
    return eckey.public_key_from_private_key(sec, addrtype)

def address_from_private_key(sec, addrtype=0, wif_version=128):
    """Deprecated."""
    return eckey.address_from_private_key(sec, addrtype, wif_version)

def is_valid(addr, active_chain=None):
    """Deprecated."""
    return base58.is_valid(addr, active_chain)

def is_address(addr, active_chain=None):
    """Deprecated."""
    return base58.is_address(addr, active_chain)

def is_private_key(key, addrtype=128):
    """Deprecated."""
    return base58.is_private_key(key, addrtype)


########### end pywallet functions #######################
def get_pubkeys_from_secret(secret):
    """Deprecated."""
    return eckey.get_pubkeys_from_secret(secret)

###################################### BIP32 ##############################

random_seed = lambda n: "%032x"%ecdsa.util.randrange( pow(2,n) )
BIP32_PRIME = 0x80000000

# Child private key derivation function (from master private key)
# k = master private key (32 bytes)
# c = master chain code (extra entropy for key derivation) (32 bytes)
# n = the index of the key we want to derive. (only 32 bits will be used)
# If n is negative (i.e. the 32nd bit is set), the resulting private key's
#  corresponding public key can NOT be determined without the master private key.
# However, if n is positive, the resulting private key's corresponding
#  public key can be determined without the master private key.
def CKD_priv(k, c, n):
    is_prime = n & BIP32_PRIME
    return _CKD_priv(k, c, util_coin.rev_hex(util_coin.int_to_hex(n,4)).decode('hex'), is_prime)

def _CKD_priv(k, c, s, is_prime):
    import hmac
    from ecdsa.util import string_to_number, number_to_string
    order = generator_secp256k1.order()
    keypair = EC_KEY(k)
    cK = GetPubKey(keypair.pubkey,True)
    data = chr(0) + k + s if is_prime else cK + s
    I = hmac.new(c, data, hashlib.sha512).digest()
    k_n = number_to_string( (string_to_number(I[0:32]) + string_to_number(k)) % order , order )
    c_n = I[32:]
    return k_n, c_n

# Child public key derivation function (from public key only)
# K = master public key
# c = master chain code
# n = index of key we want to derive
# This function allows us to find the nth public key, as long as n is
#  non-negative. If n is negative, we need the master private key to find it.
def CKD_pub(cK, c, n):
    if n & BIP32_PRIME: raise
    return _CKD_pub(cK, c, util_coin.rev_hex(util_coin.int_to_hex(n,4)).decode('hex'))

# helper function, callable with arbitrary string
def _CKD_pub(cK, c, s):
    import hmac
    from ecdsa.util import string_to_number, number_to_string
    order = generator_secp256k1.order()
    I = hmac.new(c, cK + s, hashlib.sha512).digest()
    curve = SECP256k1
    pubkey_point = string_to_number(I[0:32])*curve.generator + ser_to_point(cK)
    public_key = ecdsa.VerifyingKey.from_public_point( pubkey_point, curve = SECP256k1 )
    c_n = I[32:]
    cK_n = GetPubKey(public_key.pubkey,True)
    return cK_n, c_n


BITCOIN_HEADER_PRIV = "0488ade4"
BITCOIN_HEADER_PUB = "0488b21e"

TESTNET_HEADER_PRIV = "04358394"
TESTNET_HEADER_PUB = "043587cf"

BITCOIN_HEADERS = (BITCOIN_HEADER_PUB, BITCOIN_HEADER_PRIV)
TESTNET_HEADERS = (TESTNET_HEADER_PUB, TESTNET_HEADER_PRIV)

def _get_headers(testnet):
    """Returns the correct headers for either testnet or bitcoin, in the form
    of a 2-tuple, like (public, private)."""
    if testnet:
        return TESTNET_HEADERS
    else:
        return BITCOIN_HEADERS


def deserialize_xkey(xkey):
    """Deserializes a base58-encoded extended key.

    Returns:
        Tuple containing depth, key fingerprint, child number, chain code bytes,
        and public/private key bytes.

    """

    xkey = DecodeBase58Check(xkey)
    assert len(xkey) == 78

    xkey_header = xkey[0:4].encode('hex')
    # Determine if the key is a bitcoin key or a testnet key.
    if xkey_header in TESTNET_HEADERS:
        head = TESTNET_HEADER_PRIV
    elif xkey_header in BITCOIN_HEADERS:
        head = BITCOIN_HEADER_PRIV
    else:
        raise Exception("Unknown xkey header: '%s'" % xkey_header)

    depth = ord(xkey[4])
    fingerprint = xkey[5:9]
    child_number = xkey[9:13]
    c = xkey[13:13+32]
    if xkey[0:4].encode('hex') == head:
        K_or_k = xkey[13+33:]
    else:
        K_or_k = xkey[13+32:]
    return depth, fingerprint, child_number, c, K_or_k


# This isn't used anywhere (?)
def get_xkey_name(xkey, testnet=False):
    depth, fingerprint, child_number, c, K = deserialize_xkey(xkey)
    n = int(child_number.encode('hex'), 16)
    if n & BIP32_PRIME:
        child_id = "%d'"%(n - BIP32_PRIME)
    else:
        child_id = "%d"%n
    if depth == 0:
        return ''
    elif depth == 1:
        return child_id
    else:
        raise BaseException("xpub depth error")


def xpub_from_xprv(xprv, testnet=False):
    depth, fingerprint, child_number, c, k = deserialize_xkey(xprv)
    K, cK = get_pubkeys_from_secret(k)
    header_pub, _  = _get_headers(testnet)
    xpub = header_pub.decode('hex') + chr(depth) + fingerprint + child_number + c + cK
    return EncodeBase58Check(xpub)


def bip32_root(seed, testnet=False):
    """Gets the root extended private and public keys in base58 encoding for a seed."""
    import hmac
    header_pub, header_priv = _get_headers(testnet)
    I = hmac.new("Bitcoin seed", seed, hashlib.sha512).digest()
    master_k = I[0:32]
    master_c = I[32:]
    K, cK = get_pubkeys_from_secret(master_k)
    xprv = (header_priv + "00" + "00000000" + "00000000").decode("hex") + master_c + chr(0) + master_k
    xpub = (header_pub + "00" + "00000000" + "00000000").decode("hex") + master_c + cK
    return EncodeBase58Check(xprv), EncodeBase58Check(xpub)


def bip32_private_derivation(xprv, branch, sequence, testnet=False):
    """Derives the private/public child keys, at a given sequence, of an extended private key.

    Args:
        xrpv (str): Base58-encoded extended key.
        branch (str): First branch in the sequence.
        sequence (str): Sequence of child keys. Branches are delimited by forward slashes.
            Hardened children are denoted by an apostrophe following the index.
        testnet (bool): Whether to use testnet extended key headers.

    Returns:
        Tuple containing the base58-encoded extended private and public child keys at the given sequence.

    """
    header_pub, header_priv = _get_headers(testnet)
    depth, fingerprint, child_number, c, k = deserialize_xkey(xprv)
    assert sequence.startswith(branch)
    sequence = sequence[len(branch):]
    for n in sequence.split('/'):
        if n == '': continue
        i = int(n[:-1]) + BIP32_PRIME if n[-1] == "'" else int(n)
        parent_k = k
        k, c = CKD_priv(k, c, i)
        depth += 1

    _, parent_cK = get_pubkeys_from_secret(parent_k)
    fingerprint = hash_160(parent_cK)[0:4]
    child_number = ("%08X"%i).decode('hex')
    K, cK = get_pubkeys_from_secret(k)
    xprv = header_priv.decode('hex') + chr(depth) + fingerprint + child_number + c + chr(0) + k
    xpub = header_pub.decode('hex') + chr(depth) + fingerprint + child_number + c + cK
    return EncodeBase58Check(xprv), EncodeBase58Check(xpub)


def bip32_public_derivation(xpub, branch, sequence, testnet=False):
    """Derives the public child key, at a given sequence, of an extended public key.

    Args:
        xpub (str): Base58-encoded extended public key.
        branch (str): First branch in the sequence.
        sequence (str): Sequence of child keys. Branches are delimited by forward slashes.
            Hardened children are denoted by an apostrophe following the index.
        testnet (bool): Whether to use testnet extended key headers.

    Returns:
        Base58-encoded extended public child key at the given sequence.

    """
    header_pub, _ = _get_headers(testnet)
    depth, fingerprint, child_number, c, cK = deserialize_xkey(xpub)
    assert sequence.startswith(branch)
    sequence = sequence[len(branch):]
    for n in sequence.split('/'):
        if n == '': continue
        i = int(n)
        parent_cK = cK
        cK, c = CKD_pub(cK, c, i)
        depth += 1

    fingerprint = hash_160(parent_cK)[0:4]
    child_number = ("%08X"%i).decode('hex')
    xpub = header_pub.decode('hex') + chr(depth) + fingerprint + child_number + c + cK
    return EncodeBase58Check(xpub)


def bip32_private_key(sequence, k, chain, addrtype=128):
    """Derives the private child key at a given sequence and returns it in WIF.

    Args:
        sequence (iterable): Sequence of child key indices.
        k (str): Private key bytes.
        chain (str): Chain code bytes.
        addrtype (int): Blockchain-specific base58 version byte for private keys in WIF.

    Returns:
        WIF key (base58-encoded).

    """
    for i in sequence:
        k, chain = CKD_priv(k, chain, i)
    return SecretToASecret(k, True, addrtype)

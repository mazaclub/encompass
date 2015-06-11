"""Utility functions involving coins."""

import hashlib

COIN = 100000000

def sha256(x):
    return hashlib.sha256(x).digest()

def Hash(x):
    """SHA256d."""
    if type(x) is unicode: x=x.encode('utf-8')
    return hashlib.sha256( hashlib.sha256(x).digest() ).digest()

def rev_hex(s):
    """Reverses the bytes of a hex string."""
    return s.decode('hex')[::-1].encode('hex')


def int_to_hex(i, length=1):
    """Encodes an integer as a little-endian hex string of the given length."""
    s = hex(i)[2:].rstrip('L')
    s = "0"*(2*length - len(s)) + s
    return rev_hex(s)

def var_int(i):
    # https://en.bitcoin.it/wiki/Protocol_specification#Variable_length_integer
    if i<0xfd:
        return int_to_hex(i)
    elif i<=0xffff:
        return "fd"+int_to_hex(i,2)
    elif i<=0xffffffff:
        return "fe"+int_to_hex(i,4)
    else:
        return "ff"+int_to_hex(i,8)

def op_push(i):
    if i<0x4c:
        return int_to_hex(i)
    elif i<0xff:
        return '4c' + int_to_hex(i)
    elif i<0xffff:
        return '4d' + int_to_hex(i,2)
    else:
        return '4e' + int_to_hex(i,4)

hash_encode = lambda x: x[::-1].encode('hex')
hash_decode = lambda x: x.decode('hex')[::-1]


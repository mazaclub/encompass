import hashlib
import base64
import sys
import hmac

try:
    import ecdsa
except ImportError:
    sys.exit("Error: python-ecdsa does not seem to be installed. Try 'sudo pip install ecdsa'")

try:
    import aes
except ImportError:
    sys.exit("Error: AES does not seem to be installed. Try 'sudo pip install slowaes'")

from util import print_error
from util_coin import var_int, Hash
import base58
from base58 import bc_address_to_hash_160, public_key_to_bc_address
import chainparams

# AES encryption
EncodeAES = lambda secret, s: base64.b64encode(aes.encryptData(secret,s))
DecodeAES = lambda secret, e: aes.decryptData(secret, base64.b64decode(e))

def strip_PKCS7_padding(s):
    """return s stripped of PKCS7 padding"""
    if len(s)%16 or not s:
        raise ValueError("String of len %d can't be PCKS7-padded" % len(s))
    numpads = ord(s[-1])
    if numpads > 16:
        raise ValueError("String ending with %r can't be PCKS7-padded" % s[-1])
    if s[-numpads:] != numpads*chr(numpads):
        raise ValueError("Invalid PKCS7 padding")
    return s[:-numpads]


def aes_encrypt_with_iv(key, iv, data):
    mode = aes.AESModeOfOperation.modeOfOperation["CBC"]
    key = map(ord, key)
    iv = map(ord, iv)
    data = aes.append_PKCS7_padding(data)
    keysize = len(key)
    assert keysize in aes.AES.keySize.values(), 'invalid key size: %s' % keysize
    moo = aes.AESModeOfOperation()
    (mode, length, ciph) = moo.encrypt(data, mode, key, keysize, iv)
    return ''.join(map(chr, ciph))

def aes_decrypt_with_iv(key, iv, data):
    mode = aes.AESModeOfOperation.modeOfOperation["CBC"]
    key = map(ord, key)
    iv = map(ord, iv)
    keysize = len(key)
    assert keysize in aes.AES.keySize.values(), 'invalid key size: %s' % keysize
    data = map(ord, data)
    moo = aes.AESModeOfOperation()
    decr = moo.decrypt(data, None, mode, key, keysize, iv)
    decr = strip_PKCS7_padding(decr)
    return decr

def pw_encode(s, password):
    if password:
        secret = Hash(password)
        return EncodeAES(secret, s.encode("utf8"))
    else:
        return s


def pw_decode(s, password):
    if password is not None:
        secret = Hash(password)
        try:
            d = DecodeAES(secret, s).decode("utf8")
        except Exception:
            raise Exception('Invalid password')
        return d
    else:
        return s


################# code from pywallet ######################
def regenerate_key(sec, addrtype=128):
    """Gets the EC Key represented by a WIF key."""
    b = base58.ASecretToSecret(sec, addrtype)
    if not b:
        return False
    b = b[0:32]
    return EC_KEY(b)

def public_key_from_private_key(sec, addrtype=128):
    """Gets the public key of a WIF private key."""
    # rebuild public key from private key, compressed or uncompressed
    pkey = regenerate_key(sec, addrtype)
    assert pkey
    compressed = base58.is_compressed(sec, addrtype)
    public_key = GetPubKey(pkey.pubkey, compressed)
    return public_key.encode('hex')

def address_from_private_key(sec, addrtype=0, wif_version=128):
    """Gets the address for a WIF private key."""
    public_key = public_key_from_private_key(sec, wif_version)
    address = public_key_to_bc_address(public_key.decode('hex'), addrtype)
    return address

# pywallet openssl private key implementation

def i2d_ECPrivateKey(pkey, compressed=False):
    if compressed:
        key = '3081d30201010420' + \
              '%064x' % pkey.secret + \
              'a081a53081a2020101302c06072a8648ce3d0101022100' + \
              '%064x' % _p + \
              '3006040100040107042102' + \
              '%064x' % _Gx + \
              '022100' + \
              '%064x' % _r + \
              '020101a124032200'
    else:
        key = '308201130201010420' + \
              '%064x' % pkey.secret + \
              'a081a53081a2020101302c06072a8648ce3d0101022100' + \
              '%064x' % _p + \
              '3006040100040107044104' + \
              '%064x' % _Gx + \
              '%064x' % _Gy + \
              '022100' + \
              '%064x' % _r + \
              '020101a144034200'

    return key.decode('hex') + i2o_ECPublicKey(pkey.pubkey, compressed)

def i2o_ECPublicKey(pubkey, compressed=False):
    # public keys are 65 bytes long (520 bits)
    # 0x04 + 32-byte X-coordinate + 32-byte Y-coordinate
    # 0x00 = point at infinity, 0x02 and 0x03 = compressed, 0x04 = uncompressed
    # compressed keys: <sign> <x> where <sign> is 0x02 if y is even and 0x03 if y is odd
    if compressed:
        if pubkey.point.y() & 1:
            key = '03' + '%064x' % pubkey.point.x()
        else:
            key = '02' + '%064x' % pubkey.point.x()
    else:
        key = '04' + \
              '%064x' % pubkey.point.x() + \
              '%064x' % pubkey.point.y()

    return key.decode('hex')

# end pywallet openssl private key implementation

# This isn't used anywhere (?)
def PrivKeyToSecret(privkey):
    return privkey[9:9+32]

def GetPubKey(pubkey, compressed=False):
    return i2o_ECPublicKey(pubkey, compressed)


def GetPrivKey(pkey, compressed=False):
    return i2d_ECPrivateKey(pkey, compressed)

def GetSecret(pkey):
    return ('%064x' % pkey.secret).decode('hex')


################### end code from pywallet ########################

from ecdsa.curves import SECP256k1
from ecdsa.ellipticcurve import Point
from ecdsa.util import string_to_number, number_to_string

def get_pubkeys_from_secret(secret):
    """Gets the compressed and uncompressed public keys of a private key.

    Args:
        secret (str): Private key bytes.

    Returns:
        List of public key bytes: [uncompressed, compressed]

    """
    # public key
    private_key = ecdsa.SigningKey.from_string( secret, curve = SECP256k1 )
    public_key = private_key.get_verifying_key()
    K = public_key.to_string()
    K_compressed = GetPubKey(public_key.pubkey,True)
    return K, K_compressed

try:
    from ecdsa.ecdsa import curve_secp256k1, generator_secp256k1
except Exception:
    print "cannot import ecdsa.curve_secp256k1. You probably need to upgrade ecdsa.\nTry: sudo pip install --upgrade ecdsa"
    exit()


def msg_magic(message, active_chain=None):
    if active_chain is None:
        active_chain = chainparams.get_active_chain()
    varint = var_int(len(message))
    encoded_varint = "".join([chr(int(varint[i:i+2], 16)) for i in xrange(0, len(varint), 2)])

    # Put number of bytes before magic bytes
    coin_msg_line = "".join([ active_chain.coin_name, " Signed Message:\n" ])
    coin_msg_line = "".join([ hex(len(coin_msg_line))[2:].decode('hex'), coin_msg_line ])
    return coin_msg_line + encoded_varint + message


def verify_message(address, signature, message):
    try:
        EC_KEY.verify_message(address, signature, message)
        return True
    except Exception as e:
        print_error("Verification error: {0}".format(e))
        return False


def encrypt_message(message, pubkey):
    return EC_KEY.encrypt_message(message, pubkey.decode('hex'))


def chunks(l, n):
    return [l[i:i+n] for i in xrange(0, len(l), n)]

def ECC_YfromX(x,curved=curve_secp256k1, odd=True):
    _p = curved.p()
    _a = curved.a()
    _b = curved.b()
    for offset in range(128):
        Mx = x + offset
        My2 = pow(Mx, 3, _p) + _a * pow(Mx, 2, _p) + _b % _p
        My = pow(My2, (_p+1)/4, _p )

        if curved.contains_point(Mx,My):
            if odd == bool(My&1):
                return [My,offset]
            return [_p-My,offset]
    raise Exception('ECC_YfromX: No Y found')


def negative_point(P):
    return Point( P.curve(), P.x(), -P.y(), P.order() )


def point_to_ser(P, comp=True ):
    if comp:
        return ( ('%02x'%(2+(P.y()&1)))+('%064x'%P.x()) ).decode('hex')
    return ( '04'+('%064x'%P.x())+('%064x'%P.y()) ).decode('hex')


def ser_to_point(Aser):
    curve = curve_secp256k1
    generator = generator_secp256k1
    _r  = generator.order()
    assert Aser[0] in ['\x02','\x03','\x04']
    if Aser[0] == '\x04':
        return Point( curve, string_to_number(Aser[1:33]), string_to_number(Aser[33:]), _r )
    Mx = string_to_number(Aser[1:])
    return Point( curve, Mx, ECC_YfromX(Mx, curve, Aser[0]=='\x03')[0], _r )

class MyVerifyingKey(ecdsa.VerifyingKey):
    @classmethod
    def from_signature(klass, sig, recid, h, curve):
        """ See http://www.secg.org/download/aid-780/sec1-v2.pdf, chapter 4.1.6 """
        from ecdsa import util, numbertheory
        import msqr
        curveFp = curve.curve
        G = curve.generator
        order = G.order()
        # extract r,s from signature
        r, s = util.sigdecode_string(sig, order)
        # 1.1
        x = r + (recid/2) * order
        # 1.3
        alpha = ( x * x * x  + curveFp.a() * x + curveFp.b() ) % curveFp.p()
        beta = msqr.modular_sqrt(alpha, curveFp.p())
        y = beta if (beta - recid) % 2 == 0 else curveFp.p() - beta
        # 1.4 the constructor checks that nR is at infinity
        R = Point(curveFp, x, y, order)
        # 1.5 compute e from message:
        e = string_to_number(h)
        minus_e = -e % order
        # 1.6 compute Q = r^-1 (sR - eG)
        inv_r = numbertheory.inverse_mod(r,order)
        Q = inv_r * ( s * R + minus_e * G )
        return klass.from_public_point( Q, curve )

class EC_KEY(object):
    def __init__( self, k, active_chain=None ):
        secret = string_to_number(k)
        self.pubkey = ecdsa.ecdsa.Public_key( generator_secp256k1, generator_secp256k1 * secret )
        self.privkey = ecdsa.ecdsa.Private_key( self.pubkey, secret )
        self.secret = secret
        self.active_chain = active_chain

    def get_public_key(self, compressed=True):
        return point_to_ser(self.pubkey.point, compressed).encode('hex')

    def sign_message(self, message, compressed, address):
        private_key = ecdsa.SigningKey.from_secret_exponent( self.secret, curve = SECP256k1 )
        public_key = private_key.get_verifying_key()
        signature = private_key.sign_digest_deterministic( Hash( msg_magic(message, self.active_chain) ), hashfunc=hashlib.sha256, sigencode = ecdsa.util.sigencode_string )
        assert public_key.verify_digest( signature, Hash( msg_magic(message, self.active_chain) ), sigdecode = ecdsa.util.sigdecode_string)
        for i in range(4):
            sig = base64.b64encode( chr(27 + i + (4 if compressed else 0)) + signature )
            try:
                self.verify_message( address, sig, message)
                return sig
            except Exception:
                continue
        else:
            raise Exception("error: cannot sign message")

    @classmethod
    def verify_message(self, address, signature, message, active_chain=None):
        if getattr(self, 'active_chain', None) is not None:
            active_chain = getattr(self, 'active_chain')
        sig = base64.b64decode(signature)
        if len(sig) != 65: raise Exception("Wrong encoding")

        nV = ord(sig[0])
        if nV < 27 or nV >= 35:
            raise Exception("Bad encoding")
        if nV >= 31:
            compressed = True
            nV -= 4
        else:
            compressed = False

        recid = nV - 27
        h = Hash( msg_magic(message, active_chain) )
        public_key = MyVerifyingKey.from_signature( sig[1:], recid, h, curve = SECP256k1 )

        # check public key
        public_key.verify_digest( sig[1:], h, sigdecode = ecdsa.util.sigdecode_string)

        # check that we get the original signing address
        addrtype = bc_address_to_hash_160(address)[0]
        addr = public_key_to_bc_address( point_to_ser(public_key.pubkey.point, compressed), addrtype )
        if address != addr:
            raise Exception("Bad signature")


    # ECIES encryption/decryption methods; AES-128-CBC with PKCS7 is used as the cipher; hmac-sha256 is used as the mac

    @classmethod
    def encrypt_message(self, message, pubkey):

        pk = ser_to_point(pubkey)
        if not ecdsa.ecdsa.point_is_valid(generator_secp256k1, pk.x(), pk.y()):
            raise Exception('invalid pubkey')

        ephemeral_exponent = number_to_string(ecdsa.util.randrange(pow(2,256)), generator_secp256k1.order())
        ephemeral = EC_KEY(ephemeral_exponent)
        ecdh_key = point_to_ser(pk * ephemeral.privkey.secret_multiplier)
        key = hashlib.sha512(ecdh_key).digest()
        iv, key_e, key_m = key[0:16], key[16:32], key[32:]
        ciphertext = aes_encrypt_with_iv(key_e, iv, message)
        ephemeral_pubkey = ephemeral.get_public_key(compressed=True).decode('hex')
        encrypted = 'BIE1' + ephemeral_pubkey + ciphertext
        mac = hmac.new(key_m, encrypted, hashlib.sha256).digest()

        return base64.b64encode(encrypted + mac)

    def decrypt_message(self, encrypted):

        encrypted = base64.b64decode(encrypted)

        if len(encrypted) < 85:
            raise Exception('invalid ciphertext: length')

        magic = encrypted[:4]
        ephemeral_pubkey = encrypted[4:37]
        ciphertext = encrypted[37:-32]
        mac = encrypted[-32:]

        if magic != 'BIE1':
            raise Exception('invalid ciphertext: invalid magic bytes')

        try:
            ephemeral_pubkey = ser_to_point(ephemeral_pubkey)
        except AssertionError, e:
            raise Exception('invalid ciphertext: invalid ephemeral pubkey')

        if not ecdsa.ecdsa.point_is_valid(generator_secp256k1, ephemeral_pubkey.x(), ephemeral_pubkey.y()):
            raise Exception('invalid ciphertext: invalid ephemeral pubkey')

        ecdh_key = point_to_ser(ephemeral_pubkey * self.privkey.secret_multiplier)
        key = hashlib.sha512(ecdh_key).digest()
        iv, key_e, key_m = key[0:16], key[16:32], key[32:]
        if mac != hmac.new(key_m, encrypted[:-32], hashlib.sha256).digest():
            raise Exception('invalid ciphertext: invalid mac')

        return aes_decrypt_with_iv(key_e, iv, ciphertext)


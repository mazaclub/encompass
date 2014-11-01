from collections import namedtuple

#
# Supported blockchains are organized in named tuples.
# A ChainParams tuple contains:
#   chain_index: The index (account) used in child key derivation
#   coin_name: Name of the cryptocurrency
#   code: Abbreviated form of the cryptocurrency
#   p2pkh: Pay-to-Public-Key-Hash base58 prefix
#   p2sh: Pay-to-Script-Hash base58 prefix
#   wif: Secret key base58 prefix
#   ext_pub: Extended public key base58 prefix
#   ext_priv: Extended private key base58 prefix

ChainParams = namedtuple('ChainParams', ('chain_index', 'coin_name', 'code', 'p2pkh', 'p2sh', 'wif', 'ext_pub', 'ext_priv'))

_known_chains = (
    # Bitcoin
    ChainParams(0, 'Bitcoin', 'BTC', 0, 5, 128, '0488b21e', '0488ade4'),

    # Mazacoin
    ChainParams(1, 'Mazacoin', 'MZC', 50, 9, 224, '0488b21e', '0488ade4'),
)

_known_chain_dict = dict((i.code, i) for i in _known_chains)

_known_chain_names = [i.code for i in _known_chains]

def get_chainparam(code, property):
    code = code.upper()
    chain = _known_chain_dict.get(code)
    if chain:
        return getattr(chain, property)
    return None

def get_code_from_index(index):
    for chain in _known_chains:
        if chain.chain_index == index:
            return chain.code
    return None

def get_coin_name(code):
    return get_chainparam(code, 'coin_name')

def get_full_coin_name(code):
    return ('{0} ({1})'.format(get_coin_name(code), code.upper()))

def get_p2pkh_version(code):
    return get_chainparam(code, 'p2pkh')

def get_p2sh_version(code):
    return get_chainparam(code, 'p2sh')

def get_wif_version(code):
    return get_chainparam(code, 'wif')

def get_ext_pub_version(code):
    return get_chainparam(code, 'ext_pub')

def get_ext_priv_version(code):
    return get_chainparam(code, 'ext_priv')

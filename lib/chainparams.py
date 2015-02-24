from collections import namedtuple
import importlib
import chains
#
# Supported blockchains are organized in named tuples.
# A ChainParams tuple contains:
#   chain_index: The index (BIP-0044) used in child key derivation
#       This is just for organization, the class of the actual
#       cryptocur has the chain index as well.
#   code: Abbreviated form of the cryptocurrency
#   module_name: Name of the module containing specifics on the cryptocur
#   class_name: Name of the class implementing the cryptocur

active_chain = None

ChainParams = namedtuple('ChainParams', ('chain_index', 'code', 'module_name', 'class_name'))

_known_chains = (
    # Bitcoin
    ChainParams(0, 'BTC', 'bitcoin', 'Bitcoin'),

    # Litecoin
    ChainParams(2, 'LTC', 'litecoin', 'Litecoin'),

    # Mazacoin
    ChainParams(13, 'MZC', 'mazacoin', 'Mazacoin'),

    # Viacoin
    ChainParams(14, 'VIA', 'viacoin', 'Viacoin'),
)

_known_chain_dict = dict((i.code, i) for i in _known_chains)

_known_chain_codes = [i.code for i in _known_chains]

def get_active_chain():
    global active_chain
    return active_chain

def set_active_chain(chaincode):
    global active_chain
    active_chain = get_chain_instance(chaincode)

def is_known_chain(code):
    code = code.upper()
    if code in _known_chain_codes:
        return True
    return False

def get_params(code):
    code = code.upper()
    if code in _known_chain_codes:
        return _known_chain_dict[code]
    return None

def get_chainparam(code, property):
    code = code.upper()
    chain = _known_chain_dict.get(code)
    if chain:
        return getattr(chain, property)
    return None

def get_chain_index(code):
    return get_chainparam(code, 'chain_index')

def get_code_from_index(index):
    for chain in _known_chains:
        if chain.chain_index == index:
            return chain.code
    return None

def get_server_trust(code):
    '''Retrieve the relative amount of trust in this chain's servers'''
    instance = get_chain_instance(code)
    if instance is None: return None
    # Proof of work
    is_pow = instance.PoW
    # multiple servers
    multiple_servers = len(instance.DEFAULT_SERVERS) > 1
    # criterion -> [value, info]
    return {
        'pow': [is_pow, 'This wallet verifies Proof-of-Work'],
        'multiple_servers': [multiple_servers, 'This wallet gets data from multiple servers'],
    }

def get_chain_instance(code):
    code = code.upper()
    if not is_known_chain(code): return None
    params = get_params(code)
    module_name = params.module_name
    classmodule = importlib.import_module(''.join(['chainkey.chains.', module_name]))
    classInst = getattr(classmodule, params.class_name)
    return classInst()

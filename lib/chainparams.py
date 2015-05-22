from collections import namedtuple
import importlib
import chains

active_chain = None

ChainParams = namedtuple('ChainParams', ('chain_index', 'coin_name', 'code', 'module_name'))
"""Named tuple holding data about a supported blockchain.

Attributes:
    chain_index (int): BIP-0044 chain index of the blockchain. This is just for organization.
    coin_name (str): Full name of the blockchain.
    code (str): Abbreviated name of the blockchain.
    module_name (str): Name of the module in lib/chains/ where the relevant class is defined.

"""

_known_chains = (
    # Bitcoin
    ChainParams(0, 'Bitcoin', 'BTC', 'bitcoin'),

    # Litecoin
    ChainParams(2, 'Litecoin', 'LTC', 'litecoin'),

    # Dash
    ChainParams(5, 'Dash', 'DASH', 'dash'),
    
    # Mazacoin
    ChainParams(13, 'Mazacoin', 'MZC', 'mazacoin'),

    # Viacoin
    ChainParams(14, 'Viacoin', 'VIA', 'viacoin'),
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
    instance = get_chain_instance(code)
    if instance is None: return None
    # Proof of work
    is_pow = instance.PoW
    # servers used
    servers = len(instance.DEFAULT_SERVERS)
    # criterion -> [value, info]
    return {
        'pow': is_pow,
        'servers': servers,
    }

def get_chain_instance(code):
    """Gets an instance of the given chain's class.

    Args:
        code (str): ChainParams code of the blockchain.

    Returns:
        An instance of the blockchain's class. All blockchain
        classes derive from CryptoCur, the base class defined
        in lib/chains/cryptocur.py

    """
    code = code.upper()
    if not is_known_chain(code): return None
    params = get_params(code)
    module_name = params.module_name
    # If importing fails, try with a different path.
    try:
        classmodule = importlib.import_module(''.join(['chainkey.chains.', module_name]))
        classInst = getattr(classmodule, 'Currency')
    except (AttributeError, ImportError):
        classmodule = importlib.import_module(''.join(['lib.chains.', module_name]))
    classInst = getattr(classmodule, 'Currency')
    return classInst()

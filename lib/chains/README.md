ChainKey Modules
================

This folder contains ChainKey modules for use by Encompass. A chainkey module for a coin allows Encompass to support using that coin.

Basically, a chainkey module for a coin contains some code from its corresponding Electrum fork. The specific code needed is documented here, and in the base class CryptoCur in the file cryptocur.py.
The class for a chainkey module must derive from the CryptoCur class.

## Writing a chainkey module

### Attributes

#### Chain Params

Chainkey modules require a set of constants for identifying the coin. These include:

- `chain_index`: The BIP-0044 index used in HD key derivation.
- `coin_name`: The full coin name, such as "Bitcoin" or "Mazacoin".
- `code`: The coin's abbreviation, such as "BTC" or "MZC".
- `p2pkh_version`: Address version byte, such as 0 for Bitcoin, or 50 for Mazacoin.
- `p2sh_version`: Pay-To-Script-Hash version byte, such as 5 for Bitcoin, or 9 for Mazacoin.
- `wif_version`: Wallet Import Format version byte, such as 128 for Bitcoin, or 224 for Mazacoin.
- `DUST_THRESHOLD`: Amount of satoshis that qualify as 'dust'; 5430 for Bitcoin.
- `MIN_RELAY_TX_FEE`: Minimum fee for a transaction to be relayed; 1000 for Bitcoin.
- `RECOMMENDED_FEE`: Recommended transaction fee; 50000 for Bitcoin.
- `COINBASE_MATURITY`: Number of blocks before mined coins are mature; 100 for Bitcoin.

The following constants are not yet fully implemented, but should be included:

- `ext_pub_version`: Extended public key version bytes; "0488b21e" for Bitcoin.
- `ext_priv_version`: Extended private key version bytes; "0488ade4" for Bitcoin.

#### Hash Algorithms

Most coins use SHA256d (two rounds of SHA256) for all cases where a hash algorithm is needed. Even coins that use alternative
algorithms usually just use them for proof-of-work purposes only. If the coin uses an algorithm other than SHA256d for something,
set the corresponding attribute below to the corresponding function in coinhash.

**Note**: The `coinhash` package must be used for all coin-specific hashes. It's a collection of hash algorithms, and it makes
things a lot easier to manage. Coinhash is located (here)[https://github.com/Kefkius/coinhash].

##### Example of Alternative Hash Algorithms

|Purpose             |Algorithm      |Example of chainkey module code       |
|--------------------|---------------|--------------------------------------|
|base58 encoding     |Skein          |`base58_hash = coinhash.SkeinHash`    |
|transaction hashing |X11            |`transaction_hash = coinhash.X11Hash` |

#### Info About the Chain

In addition to those constants, some more modular information is required, including:

- `PoW`: A boolean value expressing whether or not Proof-of-Work verification is implemented.
- `block_explorers`: A dictionary of {name : URL} strings for viewing a transaction online.
- `base_units`: A dictionary of {name : decimal point} units for the coin, such as "mBTC" and "BTC".
If this is not defined, the `code` attribute from above will be used with 8 as the decimal point.

#### Optional Metadata

- `headers_url`: URL where a headers bootstrap can be downloaded. If there isn't one, do not implement this - or just assign an empty string (`""`) to it.
- `checkpoints`: A dictionary of {height: hash} values for sanity testing.

Also, the number of headers in one chunk is stored in the `chunk_size` variable. This is 2016 in Electrum.

Lastly, after the currency class definition, it is required to define a variable called `Currency` as the currency's class name. For example, `Currency = Bitcoin` in bitcoin.py, where the class name is "Bitcoin."

### Functions

All functions for verifying headers are required in a chainkey module. Most importantly, `get_target()`, `verify_chain()`, and `verify_chunk()`, but also any functions they rely on, including `header_to_string()`, `header_from_string()`, `hash_header()`, `save_chunk()`, `save_header()`, and `read_header()`.

The base class CryptoCur implements some of these functions, since they're unlikely to differ from blockchain to blockchain. They can be re-implemented in a chainkey module's class if necessary.
The functions CryptoCur implements are: `verify_chain()`, `verify_chunk()`, `header_to_string()`, `header_from_string()`, `hash_header()`, `save_chunk()`, `save_header()`, and `read_header()`.
This leaves only `get_target()` as the method that must always be implemented in a Chainkey module's class.

Note that commonly in Electrum forks, the functions `save_chunk()` and `save_header()` make a call to a function `set_local_height()`.
This call must be removed in the chainkey module, as `set_local_height()` is called elsewhere. Also note that any calls to `print_error()` may be removed, as importing that function is not required.

If an electrum fork has a custom method to call when a chain reorg occurs, it should be included in the chainkey module class as `reorg_handler()`. Otherwise, `reorg_handler()` should **not** be defined.

## Implementation

To implement a new chain after writing a chainkey module, place the coin's module in lib/chains with the others. Then edit lib/chainparams.py, adding a ChainParams named-tuple for that coin in `known_chains`. When a chain is in `known_chains`, Encompass will be able to use it as long as its metadata is correct.
In the file `lib/chains/__init__.py`, a line that says `import yourcoin`, where `yourcoin` is the name of the new chainkey module, is required.

For installation purposes, also add the module to the `py_modules` list in setup.py, as Bitcoin is done [here](https://github.com/mazaclub/encompass/blob/master/setup.py#L117).

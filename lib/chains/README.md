ChainKey Modules
================

This folder contains ChainKey modules for use by Encompass. A chainkey module for a coin allows Encompass to support using that coin.

Basically, a chainkey module for a coin contains some code from its corresponding Electrum fork. The specific code needed is documented here, and in the abstract class CryptoCur in the file cryptocur.py.

## Writing a chainkey module

### Variables

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

In addition to those constants, some more modular information is required, including:

- `block_explorers`: A dictionary of {name : URL} strings for viewing a transaction online.
- `base_units`: A dictionary of {name : decimal point} units for the coin, such as "mBTC" and "BTC".

Also, the number of headers in one chunk is stored in the `chunk_size` variable. This is 2016 in Electrum.

### Functions

All functions for verifying headers are required in a chainkey module. Most importantly, `get_target()`, `verify_chain()`, and `verify_chunk()`, but also any functions they rely on, including `set_headers_path()`, `path()`, `header_to_string()`, `header_from_string()`, `hash_header()`, `save_chunk()`, `save_header()`, and `read_header()`.

Note that commonly in Electrum forks, the functions `save_chunk()` and `save_header()` make a call to a function `set_local_height()`. This call must be removed in the chainkey module, as `set_local_height()` is called elsewhere. Also note that any calls to `print_error()` may be removed, as importing that function is not required.

If an electrum fork has a custom method to call when a chain reorg occurs, it should be included in the chainkey module class as `reorg_handler()`.

## Implementation

To implement a new chain after writing a chainkey module, place the coin's module in lib/chains with the others. Then edit lib/chainparams.py, adding a ChainParams named-tuple for that coin in `_known_chains`. When a chain is in `_known_chains`, Encompass will be able to use it as long as its metadata is correct.

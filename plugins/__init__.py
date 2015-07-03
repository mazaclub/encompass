"""Metadata about Encompass plugins."""
try:
    from chainkey.i18n import _
except Exception:
    _ = lambda s: str(s)

"""List of dicts containing plugin data.

Mandatory dictionary keys/values:

    - name (str): Short name of plugin.
    - fullname (str): Full name of plugin for humans to read.
    - description (str): Description of what the plugin does.
    - available_for (list): List of strings with GUI types the plugin applies to.
            Possible values: ['cmdline', 'qt']

Optional dictionary keys/values:

    - requires (list): Packages that the module requires to function.
    - requires_wallet_type (list): Wallet types that the plugin can work with.
    - registers_wallet_type (tuple): Wallet type that the plugin defines.
            Tuple format: (category, type, description)
    - requires_chain (list): Chain codes that the plugin can work with.
            This is a list of codes (e.g. BTC), not names (e.g. Bitcoin).

"""
plugin_data = [
    {
        'name': 'cosigner_pool',
        'fullname': 'Cosigner Pool',
        'description': ' '.join([
            _("This plugin facilitates the use of multi-signatures wallets."),
            _("It sends and receives partially signed transactions from/to your cosigner wallet."),
            _("Transactions are encrypted and stored on a remote server.")
        ]),
        'requires_wallet_type': ['2of2', '2of3', 'mofn'],
        'available_for': ['qt'],
    },
    {
        'name': 'openalias',
        'fullname': 'OpenAlias',
        'description': _('Allows for payments to OpenAlias addresses.'),
        'available_for': ['cmdline', 'qt'],
    },
    {
        'name': 'plot',
        'fullname': 'Plot History',
        'description': _('Ability to graphically plot transaction history.'),
        'requires': ['matplotlib'],
        'available_for': ['qt'],
    },
    {
        'name': 'trezor',
        'fullname': 'Trezor Wallet',
        'description': _('Provides support for Trezor hardware wallet.'),
        'requires_wallet_type': ['trezor'],
        'registers_wallet_type': ('hardware', 'trezor', _('Trezor Wallet')),
        'available_for': ['cmdline', 'qt'],
    },
    {
        'name': 'virtualkeyboard',
        'fullname': 'Virtual Keyboard',
        'description': '\n'.join([
            _("Adds an optional virtual keyboard to the password dialog."),
            _("Warning: Do not use this if it makes you pick a weaker password.")
        ]),
        'available_for': ['qt'],
    },
    {
        'name': 'autoexport',
        'fullname': 'Auto History Export',
        'description': _('Automatically exports transaction history.'),
        'available_for': ['qt'],
    }
]

"""List of dicts containing hidden plugin data.

Hidden plugins are plugins that are always loaded if their requirements are met,
and are not visible to the user. They are not in the list of displayed plugins.

The purpose of hidden plugins is to support unique features of chains by
leveraging the plugin system in addition to the chainhook system.

"""
hidden_plugin_data = [
    {
        'name': 'clamspeech',
        'fullname': 'ClamSpeech',
        'description': _('Provides support for viewing ClamSpeech in Clam transactions.'),
        'requires_chain': ['CLAMS'],
        'available_for': ['qt'],
    }
]

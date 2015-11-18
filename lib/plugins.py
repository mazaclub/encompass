import os
import imp

from util import print_error
import traceback, sys
from util import *
from i18n import _
import bitcoin

class Contacts(StoreDict):

    def __init__(self, config):
        StoreDict.__init__(self, config, 'contacts')

    def resolve(self, k, nocheck=False):
        if bitcoin.is_address(k):
            return {'address':k, 'type':'address'}
        if k in self.keys():
            _type, addr = self[k]
            if _type == 'address':
                return {'address':addr, 'type':'contact'}
        out = run_hook('resolve_address', k)
        if out:
            if not nocheck and out.get('validated') is False:
                raise Exception("cannot validate alias")
            return out
        raise Exception("invalid coin address", k)


plugins = {}
plugin_data = []
loader = None

def is_available(name, w):
    for d in plugin_data:
        if d.get('name') == name:
            break
    else:
        return False
    # import requirements
    deps = d.get('requires', [])
    for dep in deps:
        try:
            __import__(dep)
        except ImportError:
            return False
    wallet_types = d.get('requires_wallet_type')
    if wallet_types:
        if w.wallet_type not in wallet_types:
            return False
    chains = d.get('requires_chain')
    if chains:
        if w.active_chain_code not in chains:
            return False
    return True

def init_plugins(config, is_local, gui_name):
    global plugins, plugin_data, loader
    if is_local:
        fp, pathname, description = imp.find_module('plugins')
        chainkey_plugins = imp.load_module('chainkey_plugins', fp, pathname, description)
        loader = lambda name: imp.load_source('chainkey_plugins.' + name, os.path.join(pathname, name + '.py'))
    else:
        chainkey_plugins = __import__('chainkey_plugins')
        loader = lambda name: __import__('chainkey_plugins.' + name, fromlist=['chainkey_plugins'])

    def constructor(name, storage):
        """Wallet constructor.

        Calls the constructor method of the plugin.

        """
        if plugins.get(name) is None:
            try:
                print_error('Loading plugin by constructor: {}'.format(name))
                p = loader(name)
                plugins[name] = p.Plugin(config, name)
            except Exception:
                print_error('Cannot initialize plugin: {}'.format(name))
                return
        return plugins[name].constructor(storage)

    def register_wallet_type(name, x, constructor):
        import wallet
        x += (lambda storage: constructor(name, storage),)
        wallet.wallet_types.append(x)

    plugin_data = chainkey_plugins.plugin_data
    # Add hidden plugin data
    hidden_plugin_data = chainkey_plugins.hidden_plugin_data
    for d in hidden_plugin_data:
        d['hidden'] = True
    plugin_data.extend(hidden_plugin_data)
    # Load all plugins
    for item in plugin_data:
        name = item['name']
        if gui_name not in item.get('available_for', []):
            continue
        # Register plugin's wallet type
        x = item.get('registers_wallet_type')
        if x:
            register_wallet_type(name, x, constructor)
        # Stop if the plugin isn't enabled in config. Load anyway if it's a hidden plugin.
        if not config.get_above_chain('use_plugin_' + name) and not item.get('hidden', False):
            continue
        try:
            p = loader(name)
            plugins[name] = p.Plugin(config, name)
            if item.get('hidden', False):
                plugins[name].is_hidden = True
            if item.get('requires_chain', []):
                plugins[name].required_chains = item['requires_chain']
        except Exception:
            print_error('Error: Cannot initialize plugin {}'.format(name))
            traceback.print_exc(file=sys.stdout)

hook_names = set()
hooks = {}

def hook(func):
    hook_names.add(func.__name__)
    return func

def run_hook(name, *args):
    """Run plugin hooks that are enabled."""
    return _run_hook(name, False, *args)

def always_hook(name, *args):
    """Run plugin hooks regardless of whether or not they are enabled."""
    return _run_hook(name, True, *args)

def _run_hook(name, always, *args):
    results = []
    f_list = hooks.get(name, [])
    for p, f in f_list:
        if name == 'load_wallet':
            p.wallet = args[0]
        if name == 'init_qt':
            gui = args[0]
            p.window = gui.main_window
        if always or p.is_enabled():
            try:
                r = f(*args)
            except Exception:
                print_error('Plugin error: {}'.format(name))
                traceback.print_exc(file=sys.stdout)
                r = False
            if r:
                results.append(r)
        if name == 'close_wallet':
            p.wallet = None

    if results:
        assert len(results) == 1, results
        return results[0]

class BasePlugin(object):

    def __init__(self, config, name):
        self.name = name
        self.config = config
        self.wallet = None
        self.is_hidden = False
        self.required_chains = None
        # add self to hooks
        for k in dir(self):
            if k in hook_names:
                f_list = hooks.get(k, [])
                f_list.append((self, getattr(self, k)))
                hooks[k] = f_list

    def close(self):
        # remove self from hooks
        for k in dir(self):
            if k in hook_names:
                f_list = hooks.get(k, [])
                f_list.remove((self, getattr(self, k)))
                hooks[k] = f_list

    def print_error(self, *msg):
        print_error('[{}]'.format(self.name), *msg)

    def requires_settings(self):
        return False

    def enable(self):
        self.set_enabled(True)
        return True

    def disable(self):
        self.set_enabled(False)
        return True

    def init_qt(self, gui):
        pass

    @hook
    def load_wallet(self, wallet, window):
        pass

    @hook
    def close_wallet(self):
        pass

    def is_enabled(self):
        return self.is_available() and (self.config.get_above_chain('use_plugin_'+self.name) is True or self.is_hidden is True)

    def is_available(self):
        if self.required_chains and self.wallet:
            if not self.wallet.active_chain_code in self.required_chains:
                return False
        return True

    def set_enabled(self, enabled):
        if self.is_hidden:
            return
        self.config.set_key_above_chain('use_plugin_'+self.name, enabled, True)

    def settings_dialog(self):
        pass


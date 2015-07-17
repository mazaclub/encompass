import ast
import json
import threading
import os

from util import user_dir, print_error, print_msg

import chainparams
SYSTEM_CONFIG_PATH = "/etc/encompass.conf"

config = None


def get_config():
    global config
    return config


def set_config(c):
    global config
    config = c


class SimpleConfig(object):
    """
    The SimpleConfig class is responsible for handling operations involving
    configuration files.

    There are 3 different sources of possible configuration values:
        1. Command line options.
        2. User configuration (in the user's config directory)
        3. System configuration (in /etc/)
    They are taken in order (1. overrides config options set in 2., that
    override config set in 3.)

    If dormant is True, this SimpleConfig will not become global or save any changes.
    """
    def __init__(self, options=None, read_system_config_function=None,
                 read_user_config_function=None, read_user_dir_function=None, dormant=False):

        self.dormant = dormant
        # This is the holder of actual options for the current user.
        self.read_only_options = {}
        # This lock needs to be acquired for updating and reading the config in
        # a thread-safe way.
        self.lock = threading.RLock()
        # The path for the config directory. This is set later by init_path()
        self.path = None

        if options is None:
            options = {}  # Having a mutable as a default value is a bad idea.

        # The following two functions are there for dependency injection when
        # testing.
        if read_system_config_function is None:
            read_system_config_function = read_system_config
        if read_user_config_function is None:
            read_user_config_function = read_user_config
        if read_user_dir_function is None:
            self.user_dir = user_dir
        else:
            self.user_dir = read_user_dir_function

        # Save the command-line keys to make sure we don't override them.
        self.command_line_keys = options.keys()
        # Save the system config keys to make sure we don't override them.
        self.system_config_keys = []

        if options.get('portable') is not True:
            # system conf
            system_config = read_system_config_function()
            self.system_config_keys = system_config.keys()
            self.read_only_options.update(system_config)

        # update the current options with the command line options last (to
        # override both others).
        self.read_only_options.update(options)

        # init path
        self.init_path()

        # user config.
        self.user_config = read_user_config_function(self.path)

        # rare case in which there's no config section for the active chain
        # since this is accounted for in set_active_chain_code, the following accounts for
        # when the active_chain is set manually in the config fiile.
        chaincode = self.get_active_chain_code(default='MZC')
        if self.get_chain_config(chaincode) is None:
            self.set_chain_config(chaincode, {})

        if not self.dormant: set_config(self)  # Make a singleton instance of 'self'

    def init_path(self):
        # Read electrum path in the command line configuration
        self.path = self.read_only_options.get('electrum_path')

        # If not set, use the user's default data directory.
        if self.path is None:
            self.path = self.user_dir()

        # Make directory if it does not yet exist.
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        print_error( "encompass directory", self.path)

    def set_active_chain_code(self, value, save = True):
        """Easy way to account for the config being divided by chain indices"""
        value = value.upper()
        if not chainparams.is_known_chain(value):
            return False
        with self.lock:
            self.user_config['active_chain_code'] = value
            if not self.dormant:
                chainparams.set_active_chain(value)
            # Make an empty dict if nothing is there
            if self.user_config.get(value, None) is None:
                self.user_config[value] = {}
            if save:
                self.save_user_config()
        return True

    def get_active_chain_code(self, default=None):
        out = None
        with self.lock:
            out = self.user_config.get('active_chain_code', default)
        return out

    def get_above_chain(self, key, default = None):
        out = None
        with self.lock:
            out = self.read_only_options.get(key)
            if not out:
                try:
                    out = self.user_config.get(key, default)
                except KeyError:
                    out = None
        return out

    def set_key_above_chain(self, key, value, save=True):
        if not self.is_modifiable(key):
            print "Warning: not changing key '%s' because it is not modifiable" \
                  " (passed as command line option or defined in /etc/encompass.conf)"%key
        with self.lock:
            self.user_config[key] = value
            if save:
                self.save_user_config()
        return

    def get_chain_config(self, chaincode):
        '''Convenience method for getting a chain's config dict'''
        return self.get_above_chain(chaincode)

    def set_chain_config(self, chaincode, value, save=True):
        '''Convenience method for setting a chain's config dict'''
        if not chainparams.is_known_chain(chaincode):
            return False
        return self.set_key_above_chain(chaincode, value, save)

    def set_key(self, key, value, save = True):
        if not self.is_modifiable(key):
            print "Warning: not changing key '%s' because it is not modifiable" \
                  " (passed as command line option or defined in /etc/encompass.conf)"%key
            return

        active_chain_code = self.get_active_chain_code()
        with self.lock:
            try:
                self.user_config[active_chain_code][key] = value
            except KeyError:
                self.user_config[active_chain_code] = {}
                self.user_config[active_chain_code][key] = value
            if save:
                self.save_user_config()

        return

    def get(self, key, default=None):
        out = None
        active_chain_code = self.get_active_chain_code()
        with self.lock:
            out = self.read_only_options.get(key)
            if not out:
                try:
                    out = self.user_config[active_chain_code].get(key, default)
                except KeyError:
                    out = None
        return out

    def is_modifiable(self, key):
        if key in self.command_line_keys:
            return False
        if key in self.system_config_keys:
            return False
        return True

    def save_user_config(self):
        if not self.path: return
        if self.dormant: return

        path = os.path.join(self.path, "config")
        s = json.dumps(self.user_config, indent=4, sort_keys=True)
        f = open(path,"w")
        f.write( s )
        f.close()
        if self.get('gui') != 'android':
            import stat
            os.chmod(path, stat.S_IREAD | stat.S_IWRITE)

    def get_wallet_path(self):
        """Set the path of the wallet."""

        # command line -w option
        path = self.get('wallet_path')
        if path:
            return path

        # path in config file
        path = self.get('default_wallet_path')
        if path and os.path.exists(path):
            return path

        # default path
        dirpath = os.path.join(self.path, "wallets")
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)

        if self.get_above_chain('use_default_wallet', True):
            current_wallet = 'default_wallet'
        else:
            current_wallet = self.get_above_chain('current_wallet', 'default_wallet')
        new_path = os.path.join(self.path, "wallets", current_wallet)

        # default path in pre 1.9 versions
        old_path = os.path.join(self.path, "electrum.dat")
        if os.path.exists(old_path) and not os.path.exists(new_path):
            os.rename(old_path, new_path)

        return new_path


def read_system_config(path=SYSTEM_CONFIG_PATH):
    """Parse and return the system config settings in /etc/encompass.conf."""
    result = {}
    if os.path.exists(path):
        try:
            import ConfigParser
        except ImportError:
            print "cannot parse encompass.conf. please install ConfigParser"
            return

        p = ConfigParser.ConfigParser()
        try:
            p.read(path)
            for k, v in p.items('client'):
                result[k] = v
        except (ConfigParser.NoSectionError, ConfigParser.MissingSectionHeaderError):
            pass

    return result

def read_user_config(path, dormant=False):
    """Parse and store the user config settings in encompass.conf into user_config[].

    dormant: Whether the global active chain should be ignored.
    """
    if not path: return {}  # Return a dict, since we will call update() on it.

    config_path = os.path.join(path, "config")
    result = {}
    try:
        with open(config_path, "r") as f:
            data = f.read()
    except IOError:
        print_msg("Error: Cannot read config file.")
        result = {}
    try:
        result = json.loads(data)
    except:
        try:
            result = ast.literal_eval(data)
        except:
            print_msg("Error: Cannot read config file.")
            return {}

    if not type(result) is dict:
        return {}
    if not dormant:
        chainparams.set_active_chain(result.get('active_chain_code', 'BTC'))
    return result

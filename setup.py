#!/usr/bin/python

# python setup.py sdist --format=zip,gztar

from setuptools import setup
import os
import sys
import platform
import imp
del os.link

#os.system("pyrcc4 icons.qrc -o gui/qt/icons_rc.py")

version = imp.load_source('version', 'lib/version.py')

if sys.version_info[:3] < (2, 6, 0):
    sys.exit("Error: Encompass requires Python version >= 2.6.0...")
usr_share = os.path.join(sys.prefix, "share")
# presumes that user is competent if installing with additional options

if (len(sys.argv) == 1 and (sys.argv[1] == "install")): 
   if not os.access(usr_share, os.W_OK):
       try:
           os.mkdir(usr_share)
       except:
           sys.exit("Error: cannot write to %s.\nIf you do not have root permissions, you may install Encompass in a virtualenv.\nAlso, please note that you can run Encompass without installing it on your system."%usr_share)

data_files = []
if (len(sys.argv) > 1 and (sys.argv[1] == "sdist")) or (platform.system() != 'Windows' and platform.system() != 'Darwin'):
    print "Including all files"
    data_files += [
        (os.path.join(usr_share, 'applications/'), ['encompass.desktop']),
        (os.path.join(usr_share, 'app-install', 'icons/'), ['icons/encompass.png'])
    ]
    if not os.path.exists('locale'):
        os.mkdir('locale')
    for lang in os.listdir('locale'):
        if os.path.exists('locale/%s/LC_MESSAGES/electrum.mo' % lang):
            data_files.append((os.path.join(usr_share, 'locale/%s/LC_MESSAGES' % lang), ['locale/%s/LC_MESSAGES/electrum.mo' % lang]))

appdata_dir = os.path.join(usr_share, "encompass")

data_files += [
    (appdata_dir, ["data/README"])
]

# add theme data
for theme in os.listdir('data/themes'):
    if theme == 'theme_icons.qrc':
        continue
    # add theme icons
    if os.path.exists(os.path.join('data/themes', theme, 'icons')):
        data_files.append((os.path.join(appdata_dir, 'themes', theme, 'icons'),
                    map(lambda x: os.path.join('data/themes', theme, 'icons', x), os.listdir(os.path.join('data/themes', theme, 'icons')))))

    # add theme style
    theme_files = os.listdir(os.path.join('data/themes', theme))
    if 'icons' in theme_files: theme_files.remove('icons')
    data_files.append((os.path.join(appdata_dir, 'themes', theme),
                    map(lambda x: os.path.join('data/themes', theme, x), theme_files)))

for lang in os.listdir('data/wordlist'):
    data_files.append((os.path.join(appdata_dir, 'wordlist'), ['data/wordlist/%s' % lang]))


setup(
    name="Encompass",
    version=version.ELECTRUM_VERSION,
    install_requires=[
	'slowaes==0.1a1',
	'ecdsa==0.13',
	'pbkdf2==1.3',
	'requests==2.5.1',
	'pyasn1-modules==0.0.5',
	'pyasn1==0.1.7',
	'qrcode==5.1',
	'SocksiPy-branch==1.01',
	'protobuf==2.5.0',
	'tlslite==0.4.8',
	'dnspython',
	'trezor==0.6.3',
        'coinhash==1.1.4'
    ],
    dependency_links=[
        "git+https://github.com/mazaclub/python-trezor#egg=trezor"
    ],
    package_dir={
        'chainkey': 'lib',
        'chainkey_gui': 'gui',
        'chainkey_plugins': 'plugins',
    },
    scripts=['encompass'],
    data_files=data_files,
    py_modules=[
        'chainkey.account',
        'chainkey.base58',
        'chainkey.bitcoin',
        'chainkey.blockchain',
        'chainkey.bmp',
        'chainkey.chainparams',
        'chainkey.commands',
        'chainkey.daemon',
        'chainkey.eckey',
        'chainkey.hashes',
        'chainkey.i18n',
        'chainkey.interface',
        'chainkey.mnemonic',
        'chainkey.msqr',
        'chainkey.network',
        'chainkey.network_proxy',
        'chainkey.old_mnemonic',
        'chainkey.paymentrequest',
        'chainkey.paymentrequest_pb2',
        'chainkey.plugins',
        'chainkey.qrscanner',
        'chainkey.script',
        'chainkey.simple_config',
        'chainkey.synchronizer',
        'chainkey.transaction',
        'chainkey.util',
        'chainkey.util_coin',
        'chainkey.verifier',
        'chainkey.version',
        'chainkey.wallet',
        'chainkey.x509',
        'chainkey.chains.__init__',
        'chainkey.chains.bitcoin',
        'chainkey.chains.clam',
        'chainkey.chains.cryptocur',
        'chainkey.chains.mazacoin',
        'chainkey.chains.scrypt',
        'chainkey.chains.litecoin',
        'chainkey.chains.viacoin',
        'chainkey.chains.dash',
        'chainkey.chains.peercoin',
        'chainkey.chains.dogecoin',
        'chainkey.chains.blackcoin',
        'chainkey.chains.feathercoin',
        'chainkey.chains.groestlcoin',
        'chainkey.chains.namecoin',
        'chainkey.chains.startcoin',
        'chainkey.chains.parkbyte',
        'chainkey_gui.gtk',
        'chainkey_gui.qt.__init__',
        'chainkey_gui.qt.amountedit',
        'chainkey_gui.qt.console',
        'chainkey_gui.qt.currency_dialog',
        'chainkey_gui.qt.history_widget',
        'chainkey_gui.qt.icons_rc',
        'chainkey_gui.qt.installwizard',
        'chainkey_gui.qt.lite_window',
        'chainkey_gui.qt.main_window',
        'chainkey_gui.qt.mofn_dialog',
        'chainkey_gui.qt.network_dialog',
        'chainkey_gui.qt.options_dialog',
        'chainkey_gui.qt.password_dialog',
        'chainkey_gui.qt.paytoedit',
        'chainkey_gui.qt.qrcodewidget',
        'chainkey_gui.qt.qrtextedit',
        'chainkey_gui.qt.receiving_widget',
        'chainkey_gui.qt.seed_dialog',
        'chainkey_gui.qt.send_edit',
        'chainkey_gui.qt.style',
        'chainkey_gui.qt.theme_icons_rc',
        'chainkey_gui.qt.installwizard',
        'chainkey_gui.qt.transaction_dialog',
        'chainkey_gui.qt.util',
        'chainkey_gui.qt.version_getter',
        'chainkey_gui.stdio',
        'chainkey_gui.text',
        'chainkey_plugins.btchipwallet',
        'chainkey_plugins.clamspeech',
        'chainkey_plugins.coinbase_buyback',
        'chainkey_plugins.cosigner_pool',
        'chainkey_plugins.exchange_rate',
        'chainkey_plugins.greenaddress_instant',
        'chainkey_plugins.labels',
        'chainkey_plugins.openalias',
        'chainkey_plugins.trezor',
        'chainkey_plugins.virtualkeyboard',
        'chainkey_plugins.plot',

    ],
    description="Lightweight Multi-Coin Wallet",
    author="Tyler Willis, Rob Nelson, mazaclub",
    author_email="encompass-security@maza.club",
    license="GNU GPLv3",
    url="https://maza.club/encompass",
    long_description="""Lightweight Multi-Coin Wallet for Electrum-supported coins."""
)

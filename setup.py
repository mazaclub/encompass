#!/usr/bin/python

# python setup.py sdist --format=zip,gztar

from setuptools import setup
import os
import sys
import platform
import imp


version = imp.load_source('version', 'lib/version.py')
util = imp.load_source('util', 'lib/util.py')

if sys.version_info[:3] < (2, 6, 0):
    sys.exit("Error: Encompass requires Python version >= 2.6.0...")

usr_share = util.usr_share_dir()
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
    (appdata_dir, ["data/README"]),
    (os.path.join(appdata_dir, "cleanlook"), [
        "data/cleanlook/name.cfg",
        "data/cleanlook/style.css"
    ]),
    (os.path.join(appdata_dir, "sahara"), [
        "data/sahara/name.cfg",
        "data/sahara/style.css"
    ]),
    (os.path.join(appdata_dir, "dark"), [
        "data/dark/name.cfg",
        "data/dark/style.css"
    ])
]

for lang in os.listdir('data/wordlist'):
    data_files.append((os.path.join(appdata_dir, 'wordlist'), ['data/wordlist/%s' % lang]))


setup(
    name="Encompass",
    version=version.ELECTRUM_VERSION,
    install_requires=[
        'slowaes',
        'ecdsa>=0.9',
        'pbkdf2',
        'requests',
        'pyasn1',
        'pyasn1-modules',
        'qrcode',
        'SocksiPy-branch',
        'tlslite',
        'ltc_scrypt',
        'darkcoin_hash'
    ],
    dependency_links=[
        "git+https://github.com/guruvan/darkcoin_hash#egg=darkcoin_hash"
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
        'chainkey.bitcoin',
        'chainkey.blockchain',
        'chainkey.bmp',
        'chainkey.chainparams',
        'chainkey.commands',
        'chainkey.daemon',
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
        'chainkey.simple_config',
        'chainkey.synchronizer',
        'chainkey.transaction',
        'chainkey.util',
        'chainkey.verifier',
        'chainkey.version',
        'chainkey.wallet',
        'chainkey.x509',
        'chainkey.chains.__init__',
        'chainkey.chains.bitcoin',
        'chainkey.chains.cryptocur',
        'chainkey.chains.mazacoin',
        'chainkey.chains.scrypt',
        'chainkey.chains.litecoin',
        'chainkey.chains.viacoin',
        'chainkey.chains.darkcoin',        
        'chainkey_gui.gtk',
        'chainkey_gui.qt.__init__',
        'chainkey_gui.qt.amountedit',
        'chainkey_gui.qt.console',
        'chainkey_gui.qt.history_widget',
        'chainkey_gui.qt.icons_rc',
        'chainkey_gui.qt.installwizard',
        'chainkey_gui.qt.lite_window',
        'chainkey_gui.qt.main_window',
        'chainkey_gui.qt.network_dialog',
        'chainkey_gui.qt.password_dialog',
        'chainkey_gui.qt.paytoedit',
        'chainkey_gui.qt.qrcodewidget',
        'chainkey_gui.qt.qrtextedit',
        'chainkey_gui.qt.receiving_widget',
        'chainkey_gui.qt.seed_dialog',
        'chainkey_gui.qt.transaction_dialog',
        'chainkey_gui.qt.util',
        'chainkey_gui.qt.version_getter',
        'chainkey_gui.stdio',
        'chainkey_gui.text',
        'chainkey_plugins.btchipwallet',
        'chainkey_plugins.coinbase_buyback',
        'chainkey_plugins.cosigner_pool',
        'chainkey_plugins.exchange_rate',
        'chainkey_plugins.greenaddress_instant',
        'chainkey_plugins.labels',
        'chainkey_plugins.trezor',
        'chainkey_plugins.virtualkeyboard',
        'chainkey_plugins.plot',

    ],
    description="Lightweight Multi-Coin Wallet",
    author="Tyler Willis",
    author_email="kefkius@mail.com",
    license="GNU GPLv3",
    url="https://maza.club/encompass",
    long_description="""Lightweight Multi-Coin Wallet for Electrum-supported coins."""
)

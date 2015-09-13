# -*- mode: python -*-

              #'lib/util.py', 'lib/wallet.py', 'lib/simple_config.py','gui/gtk.py',
              #'lib/bitcoin.py','lib/interface.py', 'packages/trezorctl.py',
# We don't put these files in to actually include them in the script but to make the Analysis method scan them for imports
a = Analysis(['encompass', 'gui/qt/main_window.py', 'gui/qt/lite_window.py', 'gui/text.py',
             'lib/__init__.py', 'packages/trezorctl.py',
             'lib/account.py',
             'lib/base58.py',
             'lib/bitcoin.py',
             'lib/blockchain.py',
             'lib/bmp.py',
             'lib/chainparams.py',
             'lib/commands.py',
             'lib/daemon.py',
             'lib/eckey.py',
             'lib/hashes.py',
             'lib/i18n.py',
             'lib/interface.py',
             'lib/mnemonic.py',
             'lib/msqr.py',
             'lib/network.py',
             'lib/network_proxy.py',
             'lib/old_mnemonic.py',
             'lib/paymentrequest.py',
             'lib/paymentrequest_pb2.py',
             'lib/plugins.py',
             'lib/qrscanner.py',
             'lib/ripemd.py',
             'lib/script.py',
             'lib/simple_config.py',
             'lib/synchronizer.py',
             'lib/transaction.py',
             'lib/util.py',
             'lib/util_coin.py',
             'lib/verifier.py',
             'lib/version.py',
             'lib/wallet.py',
             'lib/x509.py',
              ],
             hiddenimports=["PyQt4","lib","gui","plugins","trezorlib","hid"],
             pathex=['lib','gui','plugins','packages'],
             hookspath=None)

##### include mydir in distribution #######
def extra_datas(mydir):
    def rec_glob(p, files):
        import os
        import glob
        for d in glob.glob(p):
            if os.path.isfile(d):
                files.append(d)
            rec_glob("%s/*" % d, files)
    files = []
    rec_glob("%s/*" % mydir, files)
    extra_datas = []
    for f in files:
        extra_datas.append((f, f, 'DATA'))

    return extra_datas
###########################################

# append dirs

# Theme data
a.datas += extra_datas('data')

# Localization
a.datas += extra_datas('locale')

# Py folders that are needed because of the magic import finding
a.datas += extra_datas('gui')
a.datas += extra_datas('lib')
a.datas += extra_datas('plugins')
a.datas += [ ('packages/requests/cacert.pem', 'packages/requests/cacert.pem', 'DATA') ]
a.datas += [ ('packages/trezorctl.py', 'packages/trezorctl.py', 'DATA') ]

# Dependencies
a.datas += extra_datas('packages')

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.datas,
          name=os.path.join('build/encompass/encompass', 'encompass_osx.bin'),
          debug=False,
          strip=None,
          upx=False,
          icon='icons/encompass.ico',
          console=False)
          # The console True makes an annoying black box pop up, but it does make encompass output command line commands, with this turned off no output will be given but commands can still be used

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               debug=False,
               icon='icons/encompass.ico',
               console=False,
               name=os.path.join('dist', 'encompass'))

app = BUNDLE(coll,
        name=os.path.join('dist', 'Encompass.app'),
        appname="Encompass",
        icon='encompass.icns',
        version = '0.6.0'
        )

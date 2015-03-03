# -*- mode: python -*-

# We don't put these files in to actually include them in the script but to make the Analysis method scan them for imports
a = Analysis(['encompass', 'gui/qt/main_window.py', 'gui/qt/lite_window.py', 'gui/text.py',
              'lib/util.py', 'lib/wallet.py', 'lib/simple_config.py',
              'lib/bitcoin.py','lib/interface.py'
              ],
             hiddenimports=["lib","gui"],
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

# Dependencies
a.datas += extra_datas('packages')
a.datas += extra_datas('aes')
a.datas += extra_datas('ecdsa')
a.datas += extra_datas('pyasn1')
a.datas += extra_datas('pyasn1_modules')
a.datas += extra_datas('qrcode')
a.datas += extra_datas('requests')
a.datas += extra_datas('tlslite')

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.datas,
          name=os.path.join('build\\pyi.win32\\encompass', 'encompass.exe'),
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

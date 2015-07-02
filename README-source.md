Encompass - lightweight multi-coin client

Encompass consolidates support for various currencies into one wallet. It is a BIP-0044-compliant multi-currency wallet based on Electrum. This Encompass client uses Electrum servers of supported currencies to retrieve necessary data, so no "Encompass server" is necessary.

Homepage: https://maza.club/encompass

## Operation and Installation from Source
 * Most users are encouraged to run provided release packages for their system
 * Installation from source requires python knowledge, and knowledge of package managers on your system
 * Non-Developers wishing to compile & install from source are encouraged to use the provided build system
   instructions are in contrib/encompass-release/README.md

1. GETTING STARTED
------------------

Dependencies:
 - pyqt4
 - pip
 - modules listed in requirements.txt

pyqt4 must be installed by your system package manager. 
pip is recommended for python module dependencies installation, 

 * Windows
   - TODO
 * OSX
   - we recommend macports for installing/building Encompass
     ```
     sudo port install py27-pyqt4
     sudo port install py27-pip
     ```
 * Linux 
   - Ubuntu
     ```
     sudo apt-get update
     sudo apt-get install -y python-dev python-qt4 pyqt4-dev-tools python-pip
     ```


Use pip to install all dependencies:
   ```
   pip install --upgrade -r requirements.txt
   ```
   - OSX users please note, brew, macports, and Apple each install their own python interpreters, 
   ensure that you use the correct version of pip. For macports this is usually in /opt/local/bin/pip-2.7

Use pyrcc4 to build the icons:
   ``` 
   pyrcc4 icons.qrc -o gui/qt/icons_rc.py
   pyrcc4 data/themes/theme_icons.qrc -o gui/qt/theme_icons_rc.py
   ```
If you do not have pyrcc4 on your system, you may need to install the PyQt4-devel or pyqt4-dev-tools package first.


Then to run Encompass from the source directory:
   ```
   ./encompass
   ```
You can view additional debugging messages with:
   ```
   ./encompass -v
   ```

If you wish to install Encompass on your system, you can run it from any
directory:
   ```
   sudo python setup.py install
   encompass
   ``` 
Installation from source on Linux is straightforward. 
Installation from source on Windows is possible, but not actively supported
Installation from source on OSX is possible, users should modify ./encompass to point 
to the correct python installation (i.e. macports) before installation

OSX users will likely find it easiest to build Encompass.app, and run that.
   on macports:
   ```
   /opt/local/bin/python2.7 setup.py py2app
   ```
   Resulting Encompass.app is found in the dist/ directory. 


To start Encompass from your web browser, see
http://electrum.org/bitcoin_URIs.html



2. HOW OFFICIAL PACKAGES ARE CREATED
------------------------------------

See contrib/encompass-release/README.md

3. HOW COIN-SPECIFIC MODULES ARE CREATED
----------------------------------------

See lib/chains/README.md.

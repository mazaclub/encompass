#!/bin/bash

# You probably need to update only this link
# No website as of writing (TODO)
#ELECTRUM_URL=http://electrum.bitcoin.cz/download/Electrum-1.6.1.tar.gz
#NAME_ROOT=electrum-1.6.1

# These settings probably don't need any change
export WINEPREFIX=/opt/wine-encompass
PYHOME=c:/python26
PYTHON="wine $PYHOME/python.exe -OO -B"

# Let's begin!
cd `dirname $0`
set -e

cd tmp

# Download and unpack Encompass
wget -O encompass.tgz "$ELECTRUM_URL"
tar xf encompass.tgz
mv Encompass-* encompass
rm -rf $WINEPREFIX/drive_c/encompass
cp encompass/LICENCE .
mv encompass $WINEPREFIX/drive_c

# Copy ZBar libraries to encompass
#cp "$WINEPREFIX/drive_c/Program Files (x86)/ZBar/bin/"*.dll "$WINEPREFIX/drive_c/encompass/"

cd ..

rm -rf dist/$NAME_ROOT
rm -f dist/$NAME_ROOT.zip
rm -f dist/$NAME_ROOT.exe
rm -f dist/$NAME_ROOT-setup.exe

# For building standalone compressed EXE, run:
$PYTHON "C:/pyinstaller/pyinstaller.py" --noconfirm --ascii -w --onefile "C:/encompass/encompass"

# For building uncompressed directory of dependencies, run:
$PYTHON "C:/pyinstaller/pyinstaller.py" --noconfirm --ascii -w deterministic.spec

# For building NSIS installer, run:
wine "$WINEPREFIX/drive_c/Program Files (x86)/NSIS/makensis.exe" encompass.nsi
#wine $WINEPREFIX/drive_c/Program\ Files\ \(x86\)/NSIS/makensis.exe encompass.nsis

cd dist
mv encompass.exe $NAME_ROOT.exe
mv encompass $NAME_ROOT
mv encompass-setup.exe $NAME_ROOT-setup.exe
zip -r $NAME_ROOT.zip $NAME_ROOT

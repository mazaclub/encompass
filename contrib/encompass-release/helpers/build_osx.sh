VERSION="${1}"
cd ..
sed 's/ELECTRUM_VERSION/'${VERSION}'/g' Makefile.in > Makefile
cd repo
/opt/local/bin/python2.7 setup-release.py py2app
mkdir ../src && mv dist/Encompass.app ../src/ 
cd ..
make
mkdir -pv helpers/release-packages/OSX
mv Encompass-${VERSION}.dmg helpers/release-packages/OSX
mv src/Encompass.app helpers/release-packages/OSX

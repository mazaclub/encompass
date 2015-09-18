#!/bin/bash
set -xeo pipefail
source build-config.sh
source helpers/build-common.sh
check_vars

if [ "$(uname)" = "Darwin" ];
   then
  
  if [ ! -f /opt/local/bin/python2.7 ]
  then 
    echo "This build requires macports python2.7 and pyqt4"
    exit 5
  fi  
  VER="$1"
  sed 's/ELECTRUM_VERSION/'${VER}'/g' Makefile.in > Makefile
  sed 's/ELECTRUM_VERSION/'${VER}'/g' source/osx.spec > repo/osx.spec
  cd repo
  rm -rf packages
  pip install  --no-compile -t packages -r ../helpers/requirements.txt
  #pip install  --upgrade  --no-compile -t packages -r ../helpers/requirements.txt
  cp ../python-trezor/trezorctl  packages/trezorctl.py
  /opt/local/bin/python2.7 ~/DEVEL/pyinstaller/pyinstaller.py  --onefile --windowed osx.spec
  test -d ../src || mkdir ../src 
  mv dist/Encompass.app ../src/ 
  cd ..
  test -d helpers/release-packages/OSX || mkdir -pv helpers/release-packages/OSX
  mv src/Encompass.app helpers/release-packages/OSX
  cp helpers/make_OSX-installer.sh helpers/release-packages/OSX
  pushd helpers/release-packages/OSX
  find ./ -name 'qt.conf' | xargs touch
  ./make_OSX-installer.sh $VERSION
  popd
 else
  echo "OSX Build Requires OSX build host!"                                                                                        
 fi

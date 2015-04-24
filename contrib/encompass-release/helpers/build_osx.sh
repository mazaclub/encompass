#!/bin/bash
set -xeo pipefail
VERSION="${1}"
test -z ${VERSION} && exit 1

if [ "$(uname)" = "Darwin" ];
   then
  
  if [ ! -f /opt/local/bin/python2.7 ]
  then 
    echo "This build requires macports python2.7 and pyqt4"
    exit 5
  fi  
  VER="$1"
  sed 's/ELECTRUM_VERSION/'${VER}'/g' Makefile.in > Makefile
  cd repo
  /opt/local/bin/python2.7 setup-release.py py2app
  test -d ../src || mkdir ../src 
  mv dist/Encompass.app ../src/ 
  cd ..
  #make  -  makes the unneeded dmg
  test -d helpers/release-packages/OSX || mkdir -pv helpers/release-packages/OSX
  #mv Encompass-${VER}.dmg helpers/release-packages/OSX
  mv src/Encompass.app helpers/release-packages/OSX
  cp helpers/make_OSX-installer.sh helpers/release-packages/OSX
  thisdir=$(pwd)
  cd helpers/release-packages/OSX
  ./make_OSX-installer.sh $VERSION
  cd ${thisdir}
 else
  echo "OSX Build Requires OSX build host!"                                                                                        
 fi

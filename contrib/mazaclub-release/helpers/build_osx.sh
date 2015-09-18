#!/bin/bash
set -xeo pipefail
source build-config.sh

test -z ${VERSION} && VERSION="${1}"
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
  pushd helpers/release-packages/OSX
  mkdir Encompass.app/Contents/Resources/lib/python2.7/site-packages
  pushd  Encompass.app/Contents/Resources/lib/python2.7/site-packages
  unzip ../site-packages.zip
  cd ..
  rm site-packages.zip
  mv site-packages site-packages.zip
  popd
  ./make_OSX-installer.sh $VERSION
  popd
  mv helpers/release-packages/OSX helpers/release-packages/OSX-py2app
 else
  echo "OSX Build Requires OSX build host!"                                                                                        
 fi

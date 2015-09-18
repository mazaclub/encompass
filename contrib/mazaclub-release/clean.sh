#!/bin/bash

CLEAN="$1"

all(){
 rm -rf repo
 rm prepared
 rm prepped
 rm -rf releases/*
 rm build-config.sh helpers/build-config.sh
 rm -rf source/Encompass*
 rm -rf source/encompass-setup.exe
 rm -rf ltc_scrypt*
 rm -rf helpers/release-packages
 rm -rf helpers/*.dylib
 rm -rf helpers/*.so
 rm -rf helpers/*.pyd
 rm -rf helpers/.??*
 rm -rf helpers/linux_installer.sh
 rm -rf 1.1.tar.gz*
 rm -rf darkcoin_hash*
 rm -rf groestlcoin*
 rm -rf SocksiPy*
 rm -rf helpers/.??*
 rm -rf helpers/repo
 rm -rf helpers/encompass-release
 rm -rf src/Encompass-*.dmg 
 rm -rf Makefile
 rm -rf helpers/debian_installer.sh
 rm -rf helpers/trezorctl.py
 rm -rf cython-hidapi
 rm -rf python-trezor
 rm helpers/build_release.complete
}
USER=$(whoami)
HOST=$(uname)
if [ "$HOST" = "Darwin" ]
then
  GROUP="$(groups |awk '{print $1}')"
else 
  GROUP=${USER}
fi
sudo chown -R ${USER}:${GROUP} .

case $CLEAN in 
    osx) echo "Cleaning for build_osx.sh"
         rm -rf src/Encompass.app
         rm -rf  helpers/release-packages/OSX*
         rm -rf  releases/OSX*
         rm -rf repo/build repo/dist
         ;;
windows) echo "Cleaning for build_windows.sh"
         rm -rf repo/build repo/dist
         rm -rf  helpers/release-packages/Windows*
         rm -rf  releases/Windows*
	 ;;

  linux) echo "Cleaning for build_linux.sh"
         rm helpers/linux_installer.sh
         rm -rf  helpers/release-packages/Linux*
         rm -rf  releases/Linux*
         ;;
    all) echo "Cleaning All for Fresh Build"
         all
         ;;
      *) echo "Cleaning nothing"
         exit
         ;;
esac



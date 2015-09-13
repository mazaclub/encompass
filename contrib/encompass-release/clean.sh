USER=$(whoami)
HOST=$(uname)
if [ "$HOST" = "Darwin" ]
then
  GROUP="$(groups |awk '{print $1}')"
else 
  GROUP=${USER}
fi
sudo chown -R ${USER}:${GROUP} .
rm -rf releases/*
rm -rf source/Encompass*
rm -rf source/encompass-setup.exe
rm -rf repo
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
rm -rf src Encompass-*.dmg 
rm -rf Makefile
rm -rf helpers/debian_installer.sh
rm -rf helpers/trezorctl.py
rm -rf cython-hidapi
rm -rf python-trezor
rm -rf coinhash*
rm -rf helpers/coinhash*

if [ "${1}" = all ]
then 
  rm -rf template.dmg template.dmg.bz2 wc/ wc.dmg
fi


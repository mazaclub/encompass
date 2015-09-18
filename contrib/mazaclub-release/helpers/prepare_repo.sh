#!/bin/bash
set -xeo pipefail
source build-config.sh
source helpers/build-common.sh

check_vars 

if [ ${TYPE} = "local" ]
then
  echo "Setting up Local build"
  test -d repo || mkdir -pv repo
  sudo tar -C ../../ -cpv --exclude=contrib/* . |sudo  tar -C repo -xpf -
fi  
cp -av python-trezor/trezorctl helpers/trezorctl.py
touch prepared


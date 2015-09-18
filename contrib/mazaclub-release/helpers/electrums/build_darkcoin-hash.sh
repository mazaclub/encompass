#!/bin/bash
set -xeo pipefail
source build-config.sh
source helpers/build-common.sh

check_vars
## this will be integrated into the main build in a later release
echo "Building Darkcoin_hash for Windows"
test -f 1.1.tar.gz || wget https://github.com/guruvan/darkcoin_hash/archive/1.1.tar.gz
tar -xpzvf 1.1.tar.gz
docker run -ti --rm \
  -e WINEPREFIX="/wine/wine-py2.7.8-32" \
  -v $(pwd)/darkcoin_hash-1.1:/code \
  -v $(pwd)/helpers:/helpers \
  ogrisel/python-winbuilder wineconsole --backend=curses  Z:\\helpers\\darkcoin_hash-build.bat
cp darkcoin_hash-1.1/build/lib.win32-2.7/darkcoin_hash.pyd helpers/darkcoin_hash.pyd

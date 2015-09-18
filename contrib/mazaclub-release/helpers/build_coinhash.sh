git clone https://github.com/mazaclub/coinhash
  docker run -ti --rm \
   -e WINEPREFIX="/wine/wine-py2.7.8-32" \
   -v $(pwd)/coinhash:/code \
   -v $(pwd)/helpers:/helpers \
   ogrisel/python-winbuilder wineconsole --backend=curses  Z:\\helpers\\coinhash-build.bat
   test -d helpers/coinhash || mkdir helpers/coinhash
   cp -av coinhash/build/lib.win32-2.7/coinhash/* helpers/coinhash

#!/bin/bash

cd /code/ltc_scrypt-1.0
mkdir -pv build/temp.darwin-x64
mkdir -pv build/lib.darwin-x64


x86_64-apple-darwin14-cc -fno-strict-aliasing -DNDEBUG -g -fwrapv -O2 -Wall -Wstrict-prototypes -fPIC -I./ltc_scrypt -I/usr/x86_64-apple-darwin14/SDK/MacOSX10.10.sdk/usr/include/python2.7/ -c ./scryptmodule.c -o build/temp.darwin-x64/./scryptmodule.o
x86_64-apple-darwin14-cc -fno-strict-aliasing -DNDEBUG -g -fwrapv -O2 -Wall -Wstrict-prototypes -fPIC -I./ltc_scrypt -I/usr/x86_64-apple-darwin14/SDK/MacOSX10.10.sdk/usr/include/python2.7/ -c ./scrypt.c -o build/temp.darwin-x64/./scrypt.o
x86_64-apple-darwin14-cc -shared -lpython -L/usr/x86_64-apple-darwin14/SDK/MacOSX10.10.sdk/usr/lib/ -L/usr/x86_64-apple-darwin14/lib -L/usr/x86_64-apple-darwin14/SDK/MacOSX10.10.sdk/usr/libexec/ build/temp.darwin-x64/./scryptmodule.o build/temp.darwin-x64/./scrypt.o -o build/lib.darwin-x64/ltc_scrypt.dylib

#!/bin/bash -x

cd /code
python setup.py build -x bdist_egg --plat-name=x86_64-apple-darwin14


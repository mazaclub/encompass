## Encompass Release Packaging system
 
 * Builds multiplatform release
   - currently, builds all supported platforms in single run
   - updates will include argument additions to support single-OS build, and building from develop branch

 * Requires either:
   - Linux (Ubuntu 14.04) with Docker 1.5.0 installed
   - OSX with boot2docker 1.5.0, and  macports, with python2.7, pyqt4, and pip installed
     - Homebrew should also work, with some modifications (pathnames, etc) but is untested
     - builds using default Apple python installation are discouraged. 

 * OSX buildhosts will build all all packages, Linux hosts are limited to building 
   Linux, Ubuntu, and Windows packages. 

### This contains the full and complete release process for Encompass as followed by mazaclub.

 * ** Mazaclub release packages are built via OSX in a single run with the following command: **
    ```
    ./build 0.5.0 SIGNED
    ```
    This clones https://github.com/mazaclub/encompass to
    ```
    contrib/encompass-release/repo
    ```
    and checks out the release tag specified, then runs the build scripts.

## QuickStart
   ```
   ./build version type
   ```
Types supported are:
 * local
   - build from local source - copies your local repo to a build dir, and builds
 * master
   - build from current github master
 * tagged
   - build from github tagged release
 * SIGNED
   - signed
```
   ./build 0.5.0 local
```

Currently only local and SIGNED are well tested!


All you need is docker to build a full release for Linux/OSX (native python) and Windows Setup.exe

This contains 4 primary scripts:
 - build 
   builds the docker build container,
   runs make_release inside this container
   puts all the resulting release packages and windows exe files in releases/
   and finally, makes md5 and sha1 sums and gpg signs all the sums and releases

 - helpers/make_release
   gets the current requested release tag from github and packages a release

 - helpers/make_packages helpers/make_windows helpers/make_android
   performs the packaging necessary to create tarball and windows releases

 - helpers/build-binary
   builds the windows exe files

To make adaptations, or for debugging/hacking simply change the <code>$DOCKERBIN run</code> 
to run <code>/bin/bash</code> instead of <code>/root/make_release</code>

When the build completes, you should be left with 

repo/
source/
releases/

The releases/ will contain signed & summed .tar.gz .zip  .exe and -setup.exe files for 
your release. 

This build should be easily adaptable to any electrum derived wallet. 


##### Getting started


Clone this repository and run ./build 2.0b2 (or whatever the latest stable release is) and if
all goes well your windows binary should appear in the releases folder.


##### General remarks

It's still a little hack-y - this is adapted from a few sources to provide a complete 
release packager, and intended to provide a fully deterministic build process. However, 
since the build script runs directly on the host, writing to the host's filesystem, 
and this doesn't provide the mean to specify a docker version,this is not 100% deterministic. 
A future update will include a vagrant box file to specify a build VM to run the build script.

The script also does a little extra work as we integrate it into Encompass and our release process.

There's a lot to apt-get in the Dockerfile, this will take a while to build 
the docker image. Once the docker image is built on your machine, the Encompass build 
runs quickly. 



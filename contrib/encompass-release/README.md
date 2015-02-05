#### Tate Release and Windows builder

Create (semi)unattended Tate Package Release and  Windows builds on Linux using docker.

All you need is docker to build a full release for Linux/OSX (native python) and Windows Setup.exe

This contains 4 primary scripts:
 - build 
   builds the docker build container,
   runs make_release inside this container
   puts all the resulting release packages and windows exe files in releases/
   and finally, makes md5 and sha1 sums and gpg signs all the sums and releases

 - helpers/make_release
   gets the current requested release tag from github and packages a release

 - helpers/make_packages
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


Clone this repository and run ./build 0.2 (or whatever the latest stable release is) and if
all goes well your windows binary should appear in the releases folder.


##### General remarks

It's still a little hack-y - this is adapted from a few sources to provide a complete 
release packager, and intended to provide a fully deterministic build process. However, 
since the build script runs directly on the host, writing to the host's filesystem, 
and this doesn't provide the mean to specify a docker version,this is not 100% deterministic. 
A future update will include a vagrant box file to specify a build VM to run the build script.

The script also does a little extra work as we integrate it into Tate and our release process.

There's a lot to apt-get in the Dockerfile, this will take a while to build 
the docker image. Once the docker image is built on your machine, the tate build 
runs quickly. 

# LTC_SCRYPT Windows Module
This module is build with an additional dockerimage with support for 
compiling external modules for Windows

https://github.com/ogrisel/python-winbuilder used from 
dockerhub in this release, and will be integrated into the
package/build system in a later release. 


This image is also available as an automated build on dockerhub
<code>git clone https://github.com/mazaclub/tate-winbuild && cd tate-winbuild
docker pull mazaclub/tate-winbuild
./build 0.2
</code>
Current image size is approximately 2.1GB 


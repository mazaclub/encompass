## Encompass Release Packaging system
 
 * Builds multiplatform release
 * Builds 32bit Windows release & Instaler 
 * Builds Universal 64bit Linux release with Self-Extracting CLI Installer 
 * Builds 2 64bit OSX releases and OSX Installers
   - OSX builds are produced currently by both py2app and pyinstaller
     each may have different quirks/bugs 
     py2app is prone to windowing issues (not in foreground when desired)
     pyinstaller creates binary that will segfault and fail if PyQT 
     dylibs are found in the dylib path - typically if user has macports installed
   - first run on clean build directory will configure variables, 
     download and build dependencies, cython and Windows C extensions, zip/tar sources for 
     Source release and binar packagers. 
   - if performing a SIGNED build, preparation steps cannot be re-used, all dependencies will be
     downloaded and compiled otherwise,

 * Requires either:
   - Linux (Ubuntu 14.04) with Docker 1.5.0 installed
   - OSX with boot2docker 1.5.0, and  macports, with python2.7, pyqt4, and pip installed
     - Homebrew should also work, with some modifications (pathnames, etc) but is untested
     - builds using default Apple python installation are discouraged. 

 * OSX buildhosts will build all all packages, Linux hosts are limited to building 
   Linux, and Windows packages. 

### This contains the full and complete release process for Encompass as followed by mazaclub.

 * ** Mazaclub release packages are built via OSX in a single run with the following command: **
    ```
    ./build.sh 0.5.0 SIGNED
    ```
    This clones https://github.com/mazaclub/encompass to
    ```
    contrib/mazaclub-release/repo
    ```
    and checks out the release tag specified, then runs the build scripts.

## QuickStart
   ```
   ./build.sh version type
   ./buildOSX version type
   ./buildLinux version type
   ./buildWindows version type
   ```

Types supported are:
 * local
   - build from local source - copies your local repo to a build dir, and builds
   - will reuse cached images, repos, and compiled C extensions 
   - allows for easy iteration of builds 
   - all other modes download and compile all deps and requirements
 * master
   - build from current github master
 * tagged
   - build from github tagged release
 * SIGNED
   - signed
 * TODO: develop

Currently only local and SIGNED are well tested!

Many of the scripts found in helpers/*.sh are able to be run independently, 
provided previous steps in the build are completed and cached. 

Many files are saved to helpers/ during the build process

 - clean.sh [what] 
   cleans as desired - supports a single argument:
     - "osx"      - reuibld OSX binaries
     - "linux"    - rebuild Linux binaries
     - "windows"  - rebuild Windows binaries
     - "all"      - Fresh Build


 - helpers/build-common.sh
   common functions for all helper scripts to use

 - build.sh (buildOSX buildLinux buildWindows)
   creates build-config.sh 
     - helpers/config.sh
   builds the docker build container,
   prepares build repo
     - helpers/prep_deps.sh
     - helpers/prepare_repo.sh
   runs make_release inside this container
     - helpers/build_release.sh
     - helpers/make_release
   determines the build, builds for specified OS(es)
     - build.sh:pick_build()
   puts all the resulting release packages and windows exe files in releases/
   and finally, makes md5 and sha1 sums and gpg signs all the sums and releases
     - build.sh: completeReleasePackage
 
   If the final step fails to run, any produced binaries are found in helpers/release-packages


When the build completes, you should be left with 


repo/
source/
releases/

The releases/ will contain signed & summed .tar.gz .zip  .exe and -setup.exe files for 
your release. 

This build should be easily adaptable to any electrum derived wallet. 



##### Getting started




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

Preparation Steps are only run once between full cleanings
    - first build run on clean build dir will take extra time
    - build_release.sh is run, completing prep tasks for all 3 OS versions
    - cython is compiled along with C extensions for windows
    

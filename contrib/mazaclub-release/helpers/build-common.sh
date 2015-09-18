#!/bin/bash 

die () {
 echo "Build Failure - Exiting"
 case "$1" in 
      1) echo "VERSION not set"
         exit 1
	 ;;
      2) echo "Build TYPE not set" 
         exit 2
	 ;;
      3) echo "Build Error $2"
         exit 3
	 ;;
      4) echo "DOCKER binary not found"
         exit 4
	 ;;
      *) echo "Other Error"
         exit 99
	 ;;
 esac
 }

find_docker () {
which docker || echo "docker" not found                                         
if [[ $? = 0 ]]; then
  DOCKERBIN=$(which docker)
  echo "export DOCKERBIN=$(which docker)" >> build-config.sh
  fi
}

check_vars() {
test -z $DOCKERBIN && find_docker
test -z $DOCKERBIN && die 4

test -z $VERSION && VERSION="$1"
test -z $VERSION && die 1

test -z $TYPE && TYPE="$2"
test -z $TYPE && die 2
echo "Variables set correctly "
echo "DOCKERBIN = $DOCKERBIN"
echo "VERSION = $VERSION"
echo "Build TYPE = $TYPE"
}

sign_release () {
         sha1sum ${release} > ${1}.sha1
         md5sum ${release} > ${1}.md5
         gpg --sign --armor --detach  ${1}
         gpg --sign --armor --detach  ${1}.md5
         gpg --sign --armor --detach  ${1}.sha1
}

build_win32trezor() {
 ./helpers/build-hidapi.sh
}
get_archpkg (){
  if [ "${TYPE}" = "SIGNED" ]
  then 
     archbranch="v${VERSION}"
  else
     archbranch="\"check_repo_for_correct_branch\""
  fi
  test -d ../../contrib/ArchLinux || mkdir -v ../../contrib/ArchLinux
  pushd ../../contrib/ArchLinux
  wget https://aur.archlinux.org/packages/en/encompass-git/encompass-git.tar.gz
  tar -xpzvf encompass-git.tar.gz
  sed -e 's/_gitbranch\=.*/_gitbranch='${archbranch}'/g' encompass-git/PKGBUILD > encompass-git/PKGBUILD.new
  mv encompass-git/PKGBUILD.new encompass-git/PKGBUILD
  rm encompass-git.tar.gz
  popd
}
prepare_repo(){
  ./helpers/prepare_repo.sh
}
buildRelease(){
  test -d releases || mkdir -pv $(pwd)/releases
  # echo "Making locales" 
  # $DOCKERBIN run --rm -it --privileged -e MKPKG_VER=${VERSION} -v $(pwd)/helpers:/root  -v $(pwd)/repo:/root/repo  -v $(pwd)/source:/opt/wine-electrum/drive_c/encompass/ -v $(pwd):/root/encompass-release mazaclub/encompass-release:${VERSION} /bin/bash
  echo "Making Release packages for $VERSION"
  test -f helpers/build_release.complete || ./helpers/build_release.sh
}
build_Windows(){
   echo "Making Windows EXEs for $VERSION" \
    && cp build-config.sh helpers/build-config.sh \
    && ./helpers/build_windows.sh \
    && ls -la $(pwd)/helpers/release-packages/Windows/Encompass-${VERSION}-Windows-setup.exe \
    && mv $(pwd)/helpers/release-packages/Windows $(pwd)/releases/Windows \
    && touch releases/Windows/completed
}
build_OSX(){
   echo "Attempting OSX Build: Requires Darwin Buildhost" 
  if [ "$(uname)" = "Darwin" ];
   then
   if [ ! -f /opt/local/bin/python2.7 ]
   then 
    echo "This build requires macports python2.7 and pyqt4"
    exit 5
   fi
  ./helpers/build_osx.sh ${VERSION} 
  mv helpers/release-packages/OSX helpers/release-packages/OSX-py2app
  ./helpers/build_osx-pyinstaller.sh  ${VERSION} $TYPE
 else
  echo "OSX Build Requires OSX build host!"
 fi \
   && mv $(pwd)/helpers/release-packages/OSX* $(pwd)/releases/ \
   && touch releases/OSX/completed \
   && echo "OSX build complete" 
}
build_Linux(){
   echo "Linux Packaging" \
   && ./helpers/build_linux.sh \
   && mv $(pwd)/helpers/release-packages/Linux $(pwd)/releases/Linux \
   && touch releases/Linux/completed
}
completeReleasePackage(){
#  mv $(pwd)/helpers/release-packages/* $(pwd)/releases/
  if [ "${TYPE}" = "rc" ]; then export TYPE=SIGNED ; fi
  if [ "${TYPE}" = "SIGNED" ] ; then
    ${DOCKERBIN} push mazaclub/encompass-winbuild:${VERSION}
    ${DOCKERBIN} push mazaclub/encompass-release:${VERSION}
    ${DOCKERBIN} push mazaclub/encompass32-release:${VERSION}
    ${DOCKERBIN} tag -f ogrisel/python-winbuilder mazaclub/python-winbuilder:${VERSION}
    ${DOCKERBIN} push mazaclub/python-winbuilder:${VERSION}
    cd releases
    for release in * 
    do
      if [ ! -d ${release} ]; then
         sign_release ${release}
      else
         cd ${release}
         for i in * 
         do 
           if [ ! -d ${i} ]; then
              sign_release ${i}
	   fi
         done
         cd ..
      fi
    done
  fi
  echo "You can find your Encompasss $VERSION binaries in the releases folder."
  
}

buildImage(){
  echo "Building image"
  case "${1}" in 
  winbuild) $DOCKERBIN build -t mazaclub/encompass-winbuild:${VERSION} .
         ;;
   release) $DOCKERBIN build -f Dockerfile-release -t  mazaclub/encompass-release:${VERSION} .
         ;;
  esac
}


buildLtcScrypt() {
## this will be integrated into the main build in a later release
   wget https://pypi.python.org/packages/source/l/ltc_scrypt/ltc_scrypt-1.0.tar.gz
   tar -xpzvf ltc_scrypt-1.0.tar.gz
   docker run -ti --rm \
    -e WINEPREFIX="/wine/wine-py2.7.8-32" \
    -v $(pwd)/ltc_scrypt-1.0:/code \
    -v $(pwd)/helpers:/helpers \
    ogrisel/python-winbuilder wineconsole --backend=curses  Z:\\helpers\\ltc_scrypt-build.bat
   cp -av ltc_scrypt-1.0/build/lib.win32-2.7/ltc_scrypt.pyd helpers/ltc_scrypt.pyd

}
buildCoinHash() {
  ./helpers/build_coinhash.sh
}

prepareFile(){
  echo "Preparing file for Encompass version $VERSION"
  if [ -e "$TARGETPATH" ]; then
    echo "Version tar already downloaded."
  else
   wget https://github.com/mazaclub/encompass/archive/v${VERSION}.zip -O $TARGETPATH
  fi

  if [ -d "$TARGETFOLDER" ]; then
    echo "Version is already extracted"
  else
     unzip -d $(pwd)/source ${TARGETPATH} 
  fi
}

config (){
 ./helpers/config.sh ${VERSION} ${TYPE} ${OS} 
 cat build-config.sh
}

prep_deps () {
 test -f prepped || ./helpers/prep_deps.sh
}

pick_build () {
 case "$OS" in
 
  buildWindows) echo "Windows-Only Build"
 	        build_Windows || die 99
 	       ;;
    buildLinux) echo "Linux-Only Build"
                build_Linux || die 98
 	       ;;
      buildOSX) echo "OSX-Only Build"
                build_OSX || die 97
 	       ;;
      build.sh) echo "Building Windows, Linux, and OSX"
                if [ "${TYPE}" = "local" ] ; then
		 for i in Windows Linux OSX ; do
                   test -f releases/${i}/completed || build_${i} 
		 done
                 fi || die 95
                ;;
 esac
}

test -f /.dockerenv || find_docker

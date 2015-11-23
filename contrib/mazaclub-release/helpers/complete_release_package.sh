#!/bin/bash
set -xeo pipefail
source build-config.sh
source helpers/build-common.sh

sign_release () {
         sha1sum ${1} > ${1}.sha1
	 echo "${1} SHA1 Sum:" >>  ${topdir}/Encompass-${VERSION}.sums
         cat ${1}.sha1 >> ${topdir}/Encompass-${VERSION}.sums
         md5sum ${1} > ${1}.md5
	 echo "${1} MD5 Sum:" >>  ${topdir}/Encompass-${VERSION}.sums
         cat ${1}.md5 >> ${topdir}/Encompass-${VERSION}.sums
         gpg --sign --armor --detach  ${1}
         gpg --sign --armor --detach  ${1}.md5
         gpg --sign --armor --detach  ${1}.sha1
}

   
  if [ "${TYPE}" = "SIGNED" ] ; then
    ${DOCKERBIN} push mazaclub/electrum-dash-winbuild:${VERSION}
    ${DOCKERBIN} push mazaclub/electrum-dash-release:${VERSION}
    ${DOCKERBIN} push mazaclub/electrum-dash32-release:${VERSION}
    ${DOCKERBIN} tag -f ogrisel/python-winbuilder mazaclub/python-winbuilder:${VERSION}
    ${DOCKERBIN} push mazaclub/python-winbuilder:${VERSION}
  fi

  if [ "${TYPE}" = "rc" ]; then export TYPE=SIGNED ; fi
  if [ "${TYPE}" = "SIGNED" ] ; then
cd releases
for i in * ; do
 test -f ${i}/completed && rm ${i}/completed*
done
rm -rf Windows/Encompass-${VERSION}/
rm -rf Windows/Encompass-${VERSION}.*
rm -rf Windows/Encompass-${VERSION}.*
rm -rf OSX/Encompass*tmp*
rm -rf OSX/Encompass.app
rm -rf OSX/Distribution*
rm -rf OSX/Resources
rm -rf OSX/Encompass*pre*
rm -rf OSX/make_*
cd ..
    topdir=$(pwd)

         echo "Build produced by Mazaclub" > ${topdir}/Encompass-${VERSION}.sums
      
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
      cat  ${topdir}/Encompass-${VERSION}.sums
      fi
    done
  fi
#  mv Encompass-${VERSION}.sums* releases/
  echo "You can find your Encompasss $VERSION binaries in the releases folder."

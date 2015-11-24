#!/bin/bash -l
source helpers/build-common.sh
set -xeo pipefail

# Main script
OS=$(echo $0|awk -F "/" '{print $2}')
VERSION="$1"
TYPE="$2"

echo "RUNNING CONFIG ${VERSION} ${TYPE} ${OS}"

config ${VERSION} ${TYPE} ${OS} \
 && prep_deps \
 && buildRelease \
 && pick_build 
# Build release, binaries, and packages
if [[ $? = 0 ]]; then
    echo "Build successful."
else
  echo "Seems like the build failed. Exiting."
  exit
fi

# move completed builds from helpers/release-packages to releases/
# sum and sign the binaries, zipfiles, and tarballs
completeReleasePackage ${OS}
mv Encompass-${VERSION}.sums releases/
# this is done here so we don't run this by hand on manual builds
# get all git URI/commits for build system & product 
# show config & build command line
# add it all to the .sums file and gpg sign it
echo "BUILD COMMAND: ${BUILD_CMD}"  >> releases/Encompass-${VERSION}.sums
echo "BUILD SYSTEM ==================="  >> releases/Encompass-${VERSION}.sums
echo "Built with $(grep -i url .git/config)" >> releases/Encompass-${VERSION}.sums
echo "Build system commit: $(git rev-parse HEAD  --short)" >>  releases/Encompass-${VERSION}.sums
echo "git diff: $(git diff)" >>  releases/Encompass-${VERSION}.sums
echo "PRODUCT CODE ===================" >>  releases/Encompass-${VERSION}.sums
echo "Built from $(grep -i url repo/.git/config)" >> releases/Encompass-${VERSION}.sums
echo "Built from commit $(cd repo ; git rev-parse HEAD  --short)" >>  releases/Encompass-${VERSION}.sums
echo "git diff: $(cd repo ; git diff)" >>  releases/Encompass-${VERSION}.sums
echo "BUILD CONFIG ==================="  >> releases/Encompass-${VERSION}.sums
echo "build-config.sh:" >> releases/Encompass-${VERSION}.sums
echo " " >> releases/Encompass-${VERSION}.sums
cat helpers/build-config.sh >> releases/Encompass-${VERSION}.sums
### sign the sums file if this is a public release
if [ "${TYPE}" = "rc" ] ; then
   export TYPE="SIGNED"
fi
if [ "${TYPE}" = "SIGNED" ] ; then 
   gpg --output releases/Encompass-${VERSION}.sums.asc --sign -armor --detach  releases/Encompass-${VERSION}.sums
fi


echo "End."

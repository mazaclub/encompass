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
echo "End."

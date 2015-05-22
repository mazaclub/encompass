VERSION="${1}"
test -z ${VERSION} && exit 1
PRODUCT_NAME=Encompass

set -xeo pipefail
BUILD_REPO=../../../repo
BUILT_PRODUCTS_DIR=./
INSTALL_ROOT=${PRODUCT_NAME}.app
PACKAGE_NAME=`echo "$PRODUCT_NAME" | sed "s/ /_/g"`
TMP1_ARCHIVE="${BUILT_PRODUCTS_DIR}/$PACKAGE_NAME-tmp1.pkg"
TMP2_ARCHIVE="${BUILT_PRODUCTS_DIR}/$PACKAGE_NAME-tmp2"
TMP3_ARCHIVE="${BUILT_PRODUCTS_DIR}/$PACKAGE_NAME-tmp3.pkg"
ARCHIVE_FILENAME="${BUILT_PRODUCTS_DIR}/${PACKAGE_NAME}.pkg"

test -d Resources/en.lproj || mkdir -pv Resources/en.lproj
cp -av ${BUILD_REPO}/README-OSX.md Resources/en.lproj/Readme
cp -av ${BUILD_REPO}/LICENSE Resources/en.lproj/License
cp -av ${BUILD_REPO}/icons/encompass-logo.jpg Resources/en.lproj/background



#pkgbuild --analyze --root ${INSTALL_ROOT} 'Encompass.plist'

    #--component-plist "./${PRODUCT_NAME}.plist" \
pkgbuild --root "${INSTALL_ROOT}" \
    --version "$VERSION" \
    --identifier "org.pythonmac.unspecified.${PRODUCT_NAME}" \
    --install-location "/Applications/${PRODUCT_NAME}.app" \
    "${BUILT_PRODUCTS_DIR}/${PRODUCT_NAME}-pre.pkg"

productbuild --synthesize \
    --package ${PRODUCT_NAME}-pre.pkg \
        Distribution.in
cat Distribution.in

#echo "sed"
sed -e '$ i\
 \    <title>Encompass '${VERSION}'</title>' \
 -e '$ i\
 \    <background file="background" mime-type="image/jpeg" alignment="bottomleft" scaling="proportional" />' \
 -e '$ i\
 \    <welcome file="Welcome" />'  \
 -e '$ i\
 \    <readme file="ReadMe"/>' \
 -e '$ i\
 \    <license file="License"/>' \
 -e '$ i\
 \    <conclusion file="Conclusion"/>' Distribution.in > Distribution.xml

productbuild --distribution "./Distribution.xml"  \
    --package-path "${BUILT_PRODUCTS_DIR}" \
    --resources "./Resources" \
    "${TMP1_ARCHIVE}"

# Unnecessary placeholders 
pkgutil --expand "${TMP1_ARCHIVE}" "${TMP2_ARCHIVE}"

# Patches and Workarounds

pkgutil --flatten "${TMP2_ARCHIVE}" "${TMP3_ARCHIVE}"
cp ${TMP3_ARCHIVE} ${PRODUCT_NAME}-Installer.pkg


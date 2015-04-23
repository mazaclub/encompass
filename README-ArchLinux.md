Encompass - lightweight multi-coin client

Encompass consolidates support for various currencies into one wallet. It is a BIP-0044-compliant multi-currency wallet based on Electrum. This Encompass client uses Electrum servers of supported currencies to retrieve necessary data, so no "Encompass server" is necessary.

Licence: GNU GPL v3
Author: Tyler Willis
Contributors: Thomas Voegtlin (Electrum author), mazaclub, pooler, and many more
Language: Python
Homepage: https://maza.club/encompass

1. ENCOMPASS ON ARCHLINUX
----------------------

 * Official Arch Maintainer: Qhor Vertoe
 * Official Encompass Arch repo: https://aur.archlinux.org/packages/en/encompass-git/encompass-git.tar.gz 
   - contrib/ArchLinux contains the most recent contents from the above link ** as of build time **
   - ** contrib/ArchLinux may not reflect post-build changes, version updates. **
   - you are encouraged to use the official repo, contents are mirrored here for verification
   ```
   wget https://aur.archlinux.org/packages/en/encompass-git/encompass-git.tar.gz \
    && tar -xpzvf encompass-git.tar.gz \
    && cd encompass-git \
    && mkpkg -s \
    && sudo pacman -U encompass-git-$VERSION.pkg.tar.xz
    ```

2. HOW OFFICIAL PACKAGES ARE CREATED
------------------------------------

See contrib/encompass-release/README.md for complete details on mazaclub release process

3. HOW COIN-SPECIFIC MODULES ARE CREATED
----------------------------------------

See lib/chains/README.md.

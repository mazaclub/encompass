Encompass - lightweight multi-coin client

Encompass consolidates support for various currencies into one wallet. It is a BIP-0044-compliant multi-currency wallet based on Electrum. This Encompass client uses Electrum servers of supported currencies to retrieve necessary data, so no "Encompass server" is necessary.

Licence: GNU GPL v3
Author: Tyler Willis
Contributors: Thomas Voegtlin (Electrum author), mazaclub, pooler, and many more
Language: Python
Homepage: https://maza.club/encompass

1. ENCOMPASS ON UBUNTU
----------------------

 - Installer package is provided at https://maza.club/encompass
 - To download and use:
    ```
    cd ~
    wget https://github.com/mazaclub/encompass/releases/v0.5.0/Encompass-0.5.0-Linux_x86_64.tgz
    tar -xpzvf Encompass-0.5.0-Linux_x86_64.tgz
    cd Encompass-0.5.0
    ./encompass_x86_64.bin
    ```


Once successfully installed simply type
   ```
   encompass
   ```
   Your wallets will be located in /home/YOUR_LOGIN_NAME/.encompass/wallets

Installation on 32bit machines is best achieved via github master or TAGGED branches

2. HOW OFFICIAL PACKAGES ARE CREATED
------------------------------------

See contrib/encompass-release/README.md for complete details on mazaclub release process

3. HOW COIN-SPECIFIC MODULES ARE CREATED
----------------------------------------

See lib/chains/README.md.

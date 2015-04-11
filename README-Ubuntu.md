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
 - To use simply download and:
    ```
    sudo /encompass_0.5.0_ubuntu 
    ```
    This will: 
      - extract the included .deb files for Encompass installation
      - run dpkg -i to install each of the included .deb files
      - install python-pip to your system
      - use pip to install the remaining dependencies 
      - use apt-get to clean up 

Once successfully installed simply type
   ```
   encompass
   ```
   Your wallets will be located in /home/YOUR_LOGIN_NAME/.encompass/wallets

2. HOW OFFICIAL PACKAGES ARE CREATED
------------------------------------

See contrib/encompass-release/README.md for complete details on mazaclub release process

3. HOW COIN-SPECIFIC MODULES ARE CREATED
----------------------------------------

See lib/chains/README.md.

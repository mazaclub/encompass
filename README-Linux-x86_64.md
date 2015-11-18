Encompass - lightweight multi-coin client

Encompass consolidates support for various currencies into one wallet. It is a BIP-0044-compliant multi-currency wallet based on Electrum. This Encompass client uses Electrum servers of supported currencies to retrieve necessary data, so no "Encompass server" is necessary.

Homepage: https://maza.club/encompass

1. ENCOMPASS ON LINUX
----------------------

 - Installer package is provided at https://maza.club/encompass
 - Installer is Self-Extracting Tarball with a small script viewable (with cat) at the top of this file.
 - To download and use:
    ```
    cd ~
    wget https://github.com/mazaclub/encompass/releases/v0.6.0/Encompass-0.5.0-Linux_x86_64-Installer.bin
    chmod +x Encompass-0.6.0-Linux_x86_64-Installer.bin
    ./Encompass-0.6.0-Linux_x86_64-Installer.bin
    ```
    Default is to use sudo privileges to 
      - install Encompass to /opt/encompass
      - provide symlink in /usr/loca/bin/encompass
      - install menu items/icons for all users
    Optionally, install without sudo, to installer to user home directory.
      - this is not well tested on many systems, menu items/icons may fail to appear
      
Once successfully installed simply type
   ```
   encompass
   ```
   Your wallets will be located in /home/YOUR_LOGIN_NAME/.encompass/wallets

Installation on 32bit machines is best achieved via github master or TAGGED branches
Binary versions are not provided for 32bit linux.

  ### Known Issues
   - If using the standalone executable, Themes are not supported. 


2. HOW OFFICIAL PACKAGES ARE CREATED
------------------------------------

See contrib/encompass-release/README.md for complete details on mazaclub release process

3. HOW COIN-SPECIFIC MODULES ARE CREATED
----------------------------------------

See lib/chains/README.md.

### Encompass - lightweight multi-coin client

Encompass consolidates support for various currencies into one wallet. It is a BIP-0044-compliant multi-currency wallet based on Electrum. This Encompass client uses Electrum servers of supported currencies to retrieve necessary data, so no "Encompass server" is necessary.

Homepage: https://maza.club/encompass
## Encompass on OSX

1. Download the Encompass-0.6.0_OSX-Installer.pkg from https://maza.club/encompass
2. Double click downloaded .pkg file to run Installer
3. Follow instructions to install Encompass 

Encompass will be installed by default to /Applications

Your Wallets will be stored in /Users/YOUR_LOGIN_NAME/.encompass/wallets



### KNOWN ISSUES
 - If Using the standalone executable, Themes are not available



2. HOW OFFICIAL PACKAGES ARE CREATED
------------------------------------

contrib/encompass-release

 
The 'build' script will perform all the necessary tasks to 
create a release from release-tagged github sources

If all runs correctly, you''ll find a release set in the 
contrib/encompass-release/releases directory, complete with 
md5/sha1 sums, and gpg signatures for all files. 

Additional documentation is provided in the README in that dir.
Official Releases are created with a single OSX machine, boot2docker vm and docker




3. HOW COIN-SPECIFIC MODULES ARE CREATED
----------------------------------------

See lib/chains/README.md.

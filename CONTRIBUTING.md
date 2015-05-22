### How To Contribute to Encompass 

The general workflow process is centered around git-flow & github  Pull Requests

1. Fork mazaclub/encompass to your own repo
2. Clone to your local work environment
3. cd into the newly created repo
4. Init  gitflow
5. Use gitflow to start a feature
6. complete feature
7. Push feature to your github repo
7. On github create a Pull Request from your feature branch to mazaclub/encompass:develop
8. Please comment on your PR the reason/need for your feature, and provide an example of real-world testing/usage

In general, features should be accompanied by appropriate unit tests. 
If your PR is a simple PR it will likely be accepted and merged quickly - if it is more complex, 
you are encouraged to join us in #mazaclub to discuss. 

# General Development

Use of gitflow recommended, but not required. 
All new features should be based off develop branch, not master
Feature PRs should be submitted to develop, not master

# Releases
Releases are made with gitflow, release branches are made from develop approximately every 2weeks
Release branches are merged into master and tagged.

# Bugfixes

With a rapid release cycle, most bugfixes are treated as features, and integrated into the following release. 
Non-crucial bugfixes should be integrated as *features* in the next release cycle - please follow feature workflow

Crucial bugfixes are based on master, and primarily developed by committers. 

If you have a bugfix that should or must  be merged before the next release cycle:
 - Demonstrate reproducibility 
 - Base crucial bugfixes on master
 - Submit PR from your bugfix branch via github to mazaclub/encompass:master



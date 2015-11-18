import os, sys


if getattr(sys, 'frozen', False) and sys.platform=='darwin':
      import chains.cryptocur
      from chains.cryptocur import chainhook
else: 
      import cryptocur
      from cryptocur import chainhook
if getattr(sys, 'frozen', False):
      import chains.bitcoin_chainkey
      import chains.mazacoin
      import chains.clam
      import chains.litecoin
      import chains.viacoin
      import chains.dash
      import chains.peercoin
      import chains.dogecoin
      import chains.blackcoin
      import chains.feathercoin
      import chains.groestlcoin
      import chains.namecoin
      import chains.startcoin

else:
      import bitcoin_chainkey
      import mazacoin
      import clam
      import litecoin
      import viacoin
      import dash
      import peercoin
      import dogecoin
      import blackcoin
      import feathercoin
      import groestlcoin
      import namecoin
      import startcoin


# Thrown when an interface serves a header
# that contradicts known checkpoints.
def CheckpointError(Exception):
    def __init__(self, height, checkpoint_hash, given_hash):
        self.height = height
        self.checkpoint_hash = checkpoint_hash
        self.given_hash = given_hash
    def __str__(self):
        return "Height: {}, Checkpoint hash: {}, Wrong hash: {}".format(
                            self.height, self.checkpoint_hash, self.given_hash)

import os, sys, traceback


try:
    if getattr(sys, 'frozen', False) and sys.platform=='darwin':
          from chains import cryptocur
    else:
          import cryptocur
    if getattr(sys, 'frozen', False):
          from chains import bitcoin_chainkey
          from chains import mazacoin
          from chains import clam
          from chains import litecoin
          from chains import viacoin
          from chains import dash
          from chains import peercoin
          from chains import dogecoin
          from chains import blackcoin
          from chains import feathercoin
          from chains import groestlcoin
          from chains import namecoin
          from chains import startcoin
          from chains import parkbyte

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
          import parkbyte
except Exception:
    traceback.print_exc(file=sys.stdout)
    print('ERROR: Cannot load modules for cryptocurrencies.')
    sys.exit(1)


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

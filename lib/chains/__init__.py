import cryptocur
from cryptocur import chainhook
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

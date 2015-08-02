#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2012 thomasv@ecdsa.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import os
import util
from bitcoin import *
from chains import CheckpointError


class Blockchain():
    '''Manages blockchain headers and their verification'''
    def __init__(self, config, network, active_chain):
        self.config = config
        self.network = network
        self.active_chain = active_chain
        self.headers_url = self.active_chain.headers_url
        self.local_height = 0
        self.set_local_height()

    def print_error(self, *msg):
        util.print_error("[blockchain]", *msg)

    def height(self):
        return self.local_height

    def init(self):
        self.init_headers_file()
        self.set_local_height()
        self.print_error("%d blocks" % self.local_height)

    def verify_chain(self, chain):
        return self.active_chain.verify_chain(chain)

    def verify_chunk(self, index, hexdata):
        self.active_chain.verify_chunk(index, hexdata)
        self.set_local_height()

    def header_to_string(self, res):
        return self.active_chain.header_to_string(res)

    def header_from_string(self, s):
        return self.active_chain.header_from_string(s)

    def hash_header(self, header):
        return self.active_chain.hash_header(header)

    def path(self):
        headers_file_name = '_'.join(['blockchain_headers', self.active_chain.code.lower()])
        return os.path.join(self.config.path, headers_file_name)

    def init_headers_file(self):
        filename = self.path()
        if os.path.exists(filename):
            self.active_chain.set_headers_path(filename)
            return
        # Bootstraps are temporarily disabled
#        try:
#            import urllib, socket
#            socket.setdefaulttimeout(30)
#            self.print_error("downloading ", self.headers_url )
#            urllib.urlretrieve(self.headers_url, filename)
#            self.print_error("done.")
#        except Exception:
#            self.print_error( "download failed. creating file", filename )
#            open(filename,'wb+').close()
        open(filename,'wb+').close()
        self.active_chain.set_headers_path(self.path())

    def save_chunk(self, index, chunk):
        self.active_chain.save_chunk(index, chunk)
        self.set_local_height()

    def save_header(self, header):
        self.active_chain.save_header(header)
        self.set_local_height()

    def set_local_height(self):
        name = self.path()
        if os.path.exists(name):
            h = os.path.getsize(name)/80 - 1
            if self.local_height != h:
                self.local_height = h

    def read_header(self, block_height):
        return self.active_chain.read_header(block_height)

    def get_target(self, index, chain=None):
        return self.active_chain.get_target(index, chain)

    def connect_header(self, chain, header):
        '''Builds a header chain until it connects.  Returns True if it has
        successfully connected, False if verification failed, otherwise the
        height of the next header needed.'''
        chain.append(header)  # Ordered by decreasing height
        previous_height = header['block_height'] - 1
        previous_header = self.read_header(previous_height)

        # Missing header, request it
        if not previous_header:
            return previous_height

        # Does it connect to my chain?
        prev_hash = self.hash_header(previous_header)
        if prev_hash != header.get('prev_block_hash'):
            self.print_error("reorg")
            # Call the chain's reorg handler
            self.active_chain.reorg_handler(self.local_height)
            self.set_local_height()
            return False

        # The chain is complete.  Reverse to order by increasing height
        chain.reverse()
        if self.verify_chain(chain):
            self.print_error("connected at height:", previous_height)
            for header in chain:
                self.save_header(header)
            return True

        return False

    def connect_chunk(self, idx, chunk):
        try:
            self.verify_chunk(idx, chunk)
            return idx + 1
        except CheckpointError as e:
            self.print_error('verify_chunk failed: header {} hash does not match checkpoint'.format(e.height))
            return False
        except Exception:
            self.print_error('verify_chunk failed')
            return idx - 1

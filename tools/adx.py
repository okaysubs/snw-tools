import sys
import os
import os.path as path
import struct

class ADXFile:
    MAGIC = 0x8000

    VERSION_2 = 0x2
    VERSION_3 = 0x3
    VERSION_4 = 0x5
    VERSION_4_NOLOOP = 0x6
    SUPPORTED_VERSIONS = (VERSION_2, VERSION_3, VERSION_4, VERSION_4_NOLOOP)

    ENCODING_STANDARD = 0x3
    ENCODING_EXPONENTIAL = 0x4
    ENCODING_AHX = 0x10
    ENCODING_AHX_EXPONENTIAL = 0x11
    SUPPORTED_ENCODINGS = (ENCODING_STANDARD, ENCODING_EXPONENTIAL)

    FLAG_ENCRYPTED = 0x8

    def __init__(self, filename=None):
        self.filename = None
        self.handle = None
        self.data_offset = 0
        self.encoding_type = None
        self.block_size = 0
        self.bit_depth = 0
        self.channel_count = 0
        self.sample_rate = 0
        self.sample_count = 0
        self.high_frequency = 0
        self.version = 0
        self.flags = 0
        self.has_loops = False
        self.loops = []

        if self.filename:
            self.open(filename)

    def open(self, filename):
        if self.handle:
            self.close()
        self.handle = open(filename, 'rb')

        # Check file signature.
        magic = struct.unpack('>H', self.handle.read(2))[0]
        if magic != self.MAGIC:
            raise ValueError('Not an ADX file: {} (magic = {})'.format(filename, magic))

        self.data_offset = struct.unpack('>H', self.handle.read(2))[0] + 4

        # Check for copyright offset sanity as a second signature.
        self.handle.seek(self.data_offset - 2)
        if self.handle.read(6) != b'(c)CRI':
            raise ValueError('Not an ADX file: {} (invalid copyright header)'.format(filename))
        self.handle.seek(4)

        # Read misc metadata.
        self.encoding_type, self.block_size, self.bit_depth, self.channel_count = struct.unpack('>BBBB', self.handle.read(4))
        self.sample_rate, self.sample_count = struct.unpack('>II', self.handle.read(8))
        self.high_pass_frequency, self.version, self.flags = struct.unpack('>HBB', self.handle.read(2))
        
        if self.encoding_type not in self.SUPPORTED_ENCODINGS:
            raise ValueError('Encoding scheme {} not supported by this unpacker.'.format(self.encoding_type))
        if self.version > 5:
            raise ValueError('Unsupported ADX file version. This unpacker only supports up to version 4.')

        # Reserved.
        self.handle.seek(4, os.SEEK_CUR)
        if self.version == 3:
            self.has_loops = bool(


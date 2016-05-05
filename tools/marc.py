# marc.py
# Easily extract Sora no Woto's MARC archives.
# Usage: marc.py <file> [<destdir>]

import os
import os.path as path
import sys
import struct
import collections

class MARCArchive:
    MAGIC = 0x4352414D

    def __init__(self, filename=None):
        self.verbose = 0
        self.file_count = 0
        self.handle = None
        self.filename = None
        self.offsets = []
        self.changed_files = {}
        self.added_files = []

        if filename:
            self.open(filename)

    def open(self, filename):
        if self.handle:
            self.close()
            self.handle = None

        self.filename = filename
        self.handle = open(filename, 'rb')

        magic = struct.unpack('<I', self.handle.read(4))[0]
        if magic != self.MAGIC:
            raise ValueError('Not a MARC archive: {}'.format(magic))

        self.file_count = struct.unpack('<I', self.handle.read(4))[0]
        self.log('File count: {}', self.file_count)

        self.offsets = list(struct.unpack('<' + 'I' * (self.file_count + 1), self.handle.read(4 * (self.file_count + 1))))

    def close(self):
        if self.handle:
            self.handle.close()
            self.handle = None

        self.file_count = 0
        self.handle = None
        self.filename = None
        self.offsets = []
        self.cache = collections.OrderedDict()

    def list(self):
        return [str(x) for x in range(1, self.file_count + 1)]

    def read(self, index):
        index = int(index)
        offset = self.offsets[index - 1]
        end = self.offsets[index]

        self.handle.seek(offset)
        return self.handle.read(end - offset)

    def change(self, index, contents):
        index = int(index)
        self.changed_files[index] = contents

    def add(self, name, contents):
        self.added_files.append(contents)

    def remove(self, index):
        index = int(index)
        self.files.remove(index)

    def align(self, target, boundary):
        return target + (boundary - target % boundary) % boundary

    def pad(self, handle, to):
        handle.write(b'\x00' * (to - handle.tell()))

    def save(self, target):
        if target == self.filename:
            raise ValueError('Target archive name can not be the same as open archive.')

        with open(target, 'wb') as f:
            # Header.
            f.write(struct.pack('<I', self.MAGIC))
            # Number of files.
            f.write(struct.pack('<I', self.file_count + len(self.added_files)))

            # Calculate files.
            offsets = []
            prev_offset = self.align(0x8 + 0x4 * (self.file_count + len(self.added_files)) + 0x4, 0x40)
            for i in range(self.file_count):
                if i + 1 in self.changed_files:
                    offsets.append(prev_offset)
                    prev_offset += len(self.changed_files[i + 1])
                else:
                    offsets.append(prev_offset)
                    prev_offset += self.offsets[i + 1] - self.offsets[i]
            for i in self.added_files:
                offsets.append(prev_offset)
                prev_offset += len(i)
            offsets.append(prev_offset)

            # Write header.
            f.write(struct.pack('<' + 'I' * (self.file_count + len(self.added_files) + 1), *offsets))
            self.pad(f, self.align(0x8 + 0x4 * (self.file_count + len(self.added_files)) + 0x4, 0x40))

            # Write files.
            for i in range(self.file_count):
                if i + 1 in self.changed_files:
                    f.write(self.changed_files[i + 1])
                else:
                    f.write(self.read(i + 1))
            for i in self.added_files:
                f.write(i)
                    

    def extract(self, dir):
        try:
            os.makedirs(dir)
        except:
            pass

        for i in range(self.file_count):
            self.log('Extracting {}', i + 1)

            target = path.join(dir, str(i + 1))
            with open(target, 'wb') as f:
                f.write(self.read(i + 1))

    def repack_data(self):
        return {}

    def log(self, format, *args, **kwargs):
        if self.verbose:
            print(format.format(*args, **kwargs))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        exit('Usage: {} FILE [DESTDIR]'.format(sys.argv[0]))

    if len(sys.argv) > 2:
        target = sys.argv[2]
    else:
        target = sys.argv[1]
        if target.endswith('.marc'):
            target = target[:-5]
        else:  
            target += '_files'

    arc = MARCArchive(sys.argv[1])
    arc.extract(target)


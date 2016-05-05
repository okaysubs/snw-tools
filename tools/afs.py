# afs.py
# Easily extract, modify and repack the AFS archive used by Sora no Woto.
# Usage: afs.py <file> <dest dir> <meta file>

import sys
import os
import os.path as path
import struct
import time
import datetime
import collections
import pickle

class AFSArchive:
    MAGIC = 0x00534641
    BOUNDARY = 2048
    SLOGAN = b'This file has been packed by afs.py, freely available from https://salty-salty-studios.com/shiz/code/afs.py. Have a nice day, alright?'
 
    def __init__(self, filename=None):
        self.verbose = False
        self.file_count = 0
        self.meta_offset = 0
        self.handle = None
        self.filename = None
        self.files = collections.OrderedDict()
        self.cache = collections.OrderedDict()
        self.original_order = []

        if filename:
            self.open(filename)

    def open(self, filename):
        if self.handle:
            self.close()

        self.filename = filename
        self.handle = open(filename, 'rb')
        
        magic = struct.unpack('<I', self.handle.read(4))[0]
        if magic != self.MAGIC:
            raise ValueError('Not a valid AFS archive: {}'.format(magic))

        self.file_count = struct.unpack('<I', self.handle.read(4))[0]
        self.log('File count: {}', self.file_count)

        files = []
        for _ in range(0, self.file_count):
            # Offset: 32-bit unsigned int.
            offset = struct.unpack('<I', self.handle.read(4))[0]
            # Size: 32-bit unsigned int.
            size = struct.unpack('<I', self.handle.read(4))[0]
            files.append((offset, size))
        
        self.meta_offset = struct.unpack('<I', self.handle.read(4))[0]
        self.handle.seek(self.meta_offset)
        for i in range(0, self.file_count):
            # Name: 32-byte ASCII value right-padded with null bytes.
            name = self.handle.read(32).decode('us-ascii').rstrip('\x00')
            # Date: 6 16-bit unsigned ints indicating the year, month, day, hour, minute and second.
            year, month, day, hour, minute, second = struct.unpack('<HHHHHH', self.handle.read(12))
            # No idea. Dummy?
            self.handle.read(4)

            # Get previously collected data from file and merge it into self.files.
            offset, size = files[i]
            ftime = datetime.datetime(year, month, day, hour, minute, second)

            if name not in self.files:
                self.files[name] = []
            self.files[name].append((offset, size, ftime))
            self.original_order.append((name, len(self.files[name])))

    def align(self, target):
        return target + (self.BOUNDARY - target % self.BOUNDARY) % self.BOUNDARY

    def pad(self, handle, to):
        handle.write(b'\x00' * (to - handle.tell()))

    def calculate_order(self):
        order = []

        for category, files in self.files.items():
            if category in self.cache:
                category_files = sorted(self.cache[category].keys())
            else:
                category_files = []

            for i in range(len(files)):
                # Write files in order. Cached files have an index, too. Write earlier-indexed files before the current.
                while category_files:
                    first = category_files.pop(0)
                    if first >= i:
                        category_files.insert(0, first)
                        break

                    order.append((category, first + 1))

                # Obviously replace file by cached file.
                if category in self.cache and i in category_files:
                    category_files.remove(i)

                order.append((category, i + 1))

            # Write remaining category cache indexes.
            for i in category_files:
                order.append((category, i + 1))

        # Write remaining cache indexes.
        for category, files in self.cache.items():
            if category in self.files.keys():
                continue
            for i in sorted(files.keys()):
                order.append((category, i + 1))

        return order

    def save(self, filename, order=None):
        if filename == self.filename:
            raise ValueError('File name to save to can\'t be the same as already opened file name.')
        
        with open(filename, 'wb') as target:
            # Magic.
            target.write(struct.pack('<I', self.MAGIC))
            # Number of files.
            nfiles = len(self.list())
            target.write(struct.pack('<I', nfiles))
            
            # File offsets and sizes. 8 bytes for the index, 8 per file and 8 for the meta-index.
            offset = self.align(8 + nfiles * 8 + 8)
            foffset = offset
            # Offset off the slogan we have written.
            soffset = 0
            # Meta-index to build.
            meta_index = b''
            # Order to write files in.
            order = order or self.calculate_order()

            def write_index_entry(category, size, ftime):
                nonlocal target, meta_index, soffset, foffset
                # File offset.
                target.write(struct.pack('<I', foffset))
                # File size.
                target.write(struct.pack('<I', size))

                t = ftime.timetuple()
                # File directory.
                meta_index += category.ljust(32, '\x00').encode('us-ascii')
                # File time.
                meta_index += struct.pack('<HHHHHH', t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
                # Use unused bits for a nice slogan.
                meta_index += self.SLOGAN[soffset:soffset+4].rjust(4)

                # Recalculate offsets.
                soffset = (soffset + 4) % len(self.SLOGAN)
                foffset = self.align(foffset + size)

            def write_file_entry(contents, size):
                nonlocal target, offset
                # Pad to boundary.
                self.pad(target, offset)
                # Write file, recalculate offset.
                target.write(contents)
                offset = self.align(offset + size)

            # Write primary index.
            for category, index in order:
                if category in self.cache and index - 1 in self.cache[category]:
                    size = len(self.cache[category][index - 1][0])
                    ftime = self.cache[category][index - 1][1]
                else:
                    size = self.files[category][index - 1][1]
                    ftime = self.files[category][index - 1][2]
                write_index_entry(category, size, ftime)

            # Meta-index offset and length.
            target.write(struct.pack('<I', foffset))
            target.write(struct.pack('<I', len(meta_index)))

            # Write file contents.
            for category, index in order:
                if category in self.cache and index - 1 in self.cache[category]:
                    contents = self.cache[category][index - 1][0]
                    size = len(contents)
                else:
                    contents = self.read(category, index)
                    size = self.files[category][index - 1][1]
                write_file_entry(contents, size)

            # Write meta-index.
            self.pad(target, offset)
            target.write(meta_index)

    def close(self):
        if self.handle:
            self.handle.close()
            self.handle = None
        self.file_count = 0
        self.meta_offset = 0
        self.files = collections.OrderedDict()
        self.filename = None
        self.cache = collections.OrderedDict()
        self.original_order = []

    def is_directory(self, name):
        return len(self.files.get(name, [])) + len(self.cache.get(name, [])) > 1

    def read(self, name, index=None):
        if self.is_directory(name):
            if index is None:
                raise ValueError('Can\'t read directory {} without knowing the file index to read.'.format(name))
            elif index > len(self.files[name]) or index < 1:
                raise ValueError('Invalid file index to read from {}: {}.'.format(name, index))
        if index is None:
            index = 1

        # Return cached, modified data if available, else read directly from the archive.
        if name in self.cache and index - 1 in self.cache[name]:
            data, ftime = self.cache[name][index - 1]
            return data

        offset, size, ftime = self.files[name][index - 1]

        self.handle.seek(offset)
        return self.handle.read(size)

    def change(self, name, contents, index=None, time=None):
        if name not in self.cache:
            self.cache[name] = {}
        if index is None:
            index = 1
        self.cache[name][index - 1] = contents, time or datetime.datetime.now()

    def add(self, name, contents, time=None):
        if name not in self.cache:
            self.cache[name] = {}
        self.cache[name][len(self.cache[name])] = contents, time or datetime.datetime.now()
        return len(self.cache[name])

    def remove(self, name, index=None):
        if self.is_directory(name):
            if index is None:
                if name in self.cache:
                    del self.cache[name]
                if name in self.files:
                    del self.files[name]
            else:
                if name in self.cache and index - 1 in self.cache[name].keys():
                    del self.cache[name][index - 1]
                if name in self.files and index - 1 < len(self.cache[name]):
                    del self.files[name][index - 1]
        else:
            if name in self.files:
                del self.files[name]
            if name in self.cache:
                del self.cache[name]

    def list(self):
        merged_list = []

        for category, data in self.files.items():
            if len(data) > 1:
                merged_list.extend('{}/{}'.format(category, x) for x in range(1, len(data) + 1))
            else:
                merged_list.append(category)

        for category, data in self.cache.items():
            l = len(data)
            if category in self.files.keys():
                l += len(self.files[category])
            if l > 1:
                for x in data.keys():
                    name = '{}/{}'.format(category, x)
                    if name not in merged_list:
                        merged_list.append(name)
            elif category not in merged_list:
                merged_list.append(category)

        return merged_list

    def extract(self, target_dir):
        try:
            os.makedirs(target_dir)
        except:
            pass

        def extract_from_handle(name, offset, size, ftime):
            self.log('Extracting {} (offset = {}, size = {}, time = {})'.format(name, offset, size, ftime))
            target = path.join(target_dir, name)

            self.handle.seek(offset)
            with open(target, 'wb') as f:
                f.write(self.handle.read(size))

            unixtime = time.mktime(ftime.timetuple())
            os.utime(target, (unixtime, unixtime))

        def extract_from_cache(name, contents, ftime):
            self.log('Extracting {} (time = {})'.format(name, ftime))
            target = path.join(target_dir, name)

            with open(target, 'wb') as f:
                f.write(contents)

            unixtime = time.mktime(ftime.timetuple())
            os.utime(target, (unixtime, unixtime))

        for category, files in self.files.items():
            if len(files) > 1:
                base = path.join(target_dir, category)
                try:
                    os.makedirs(base)
                except:
                    pass

                for i, (offset, size, ftime) in enumerate(files):
                    if category in self.cache and i in self.cache[category].keys():
                        continue
                    target = path.join(category, str(i + 1))
                    extract_from_handle(target, offset, size, ftime)
            else:
                if category in self.cache:
                    continue
                offset, size, ftime = files[0]
                extract_from_handle(category, offset, size, ftime)

        for category, files in self.cache.items():
            if len(files) > 1:
                base = path.join(target_dir, category)
                try:
                    os.makedirs(base)
                except:
                    pass

                for i, (contents, ftime) in enumerate(files):
                    target = path.join(category, str(i + 1))
                    extract_from_cache(target, contents, ftime)
            else:
                contents, ftime = files[0]
                extract_from_cache(category, contents, ftime)

    def repack_data(self):
        return { 'order': self.original_order }

    def log(self, format, *args, **kwargs):
        if self.verbose:
            print(format.format(*args, **kwargs))


if __name__ == "__main__":
    if len(sys.argv) < 4:
        exit("Usage: {} FILE DESTDIR METAFILE".format(sys.argv[0]))

    arc = AFSArchive(sys.argv[1])
    arc.extract(sys.argv[2])
    pickle.dump(arc.repack_data(), sys.argv[3], protocol=-1)

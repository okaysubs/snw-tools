import sys
import os
import os.path as path
import pickle

import afs
import marc
import mtexsplice
# import gim
import ev
import font
import time
import config

NEWCOLORMAPS = True

def repack(**meta):
    #exit(list(reversed(list(meta['files'].items()))))
    for file, fmeta in reversed(list(meta['files'].items())):
        ar = None
        print('repacking {} at {}'.format(fmeta['type'], file))
        if fmeta['type'] == 'afs':
            ar = afs.AFSArchive()
        elif fmeta['type'] == 'marc':
            ar = marc.MARCArchive()

        if ar:
            for f in fmeta['files']:
                with open(path.join(file, f), 'rb') as h:
                    ar.add(f.split('/')[0], h.read())
            a = False
            while not a:
                try:
                    os.rename(file, file + '_files')
                    a = True
                except:
                    time.sleep(1)
                    print('didn\'t get permission, retrying')
            ar.save(file, **fmeta['repack'])
            ar.close()
        elif fmeta['type'] == 'mtex':
            if fmeta['hash'] != config.hashfile(file+'.png'):
                mtexsplice.image_into_mtex(file, file + '.png', file + '_mtex', NEWCOLORMAPS)
                os.unlink(file)
                os.rename(file + '_mtex', file)
        #elif fmeta['type'] == 'gim':
        #    gim.image_to_gim(file + '.png', file, **fmeta['repack'])
        elif fmeta['type'] == 'ev':
            if fmeta['hash'] != config.hashfile(file+'.txt'):
                ev.load(fmeta['repack'], file+'.txt', file)

                # some script files require their end to be 64 byte aligned (else UI elements get corrupted. don't ask me why)
                name = file.replace("\\", "/")
                if name.endswith("AR000/6/5") or name.endswith("AR000/11/1"):
                    fix_zero_padded_script_files(file)
            else:
                print("translation missing")
        elif fmeta['type'] == 'font':
            if fmeta['hash'] != config.hashfile(file+'.png'):
                font.uncodepage(file+'.png', file)
        elif fmeta['type'] == 'string':
            if fmeta['hash'] != config.hashfile(file+'.txt'):
                ev.loadstringfile(file+'.txt', file)
            else:
                print("translation missing")
        else:
            raise ValueError('Unknown file type: {}'.format(file))

def fix_zero_padded_script_files(file):
    with open(file, "rb") as f:
        data = f.read()

    print("AR000_6_5 size is", len(data))

    if len(data) % 0x40:
        data += b'\x00' * (0x40 - (len(data) % 0x40))

    print("AR000_6_5 fixed size is", len(data))

    with open(file, "wb") as f:
        f.write(data)

if len(sys.argv) < 2:
    exit('usage: {} METAFILE'.format(sys.argv[0]))

with open(sys.argv[1], 'rb') as f:
    meta = pickle.load(f)
    repack(**meta)

import sys
import os
import os.path as path
import pickle
import struct
import collections

import afs
import marc
import mtex
#import gim
import ev
import font

import config
import time

if len(sys.argv) < 3:
    exit('usage: {} <start> <meta> [full]'.format(sys.argv[0]))

def extract(file, extract_files = True, toplevel = False):
    meta = collections.OrderedDict()
    if path.isdir(file):
        for f in os.listdir(file):
            meta.update(extract(path.join(file, f)))
    elif fullextract or (path.basename(file) not in config.skipfolders and path.basename(path.dirname(file)) not in config.skipfolders):
        with open(file, 'rb') as f:
            magic = struct.unpack('<I', f.read(4))[0]

        if magic == afs.AFSArchive.MAGIC:
            meta[file] = { 'type': 'afs' }
            print('Found a {} at {}'.format(meta[file]['type'], file), file=logfile)
            ar = afs.AFSArchive(file)
        elif magic == marc.MARCArchive.MAGIC:
            meta[file] = { 'type': 'marc' }
            print('Found a {} at {}'.format(meta[file]['type'], file), file=logfile)
            ar = marc.MARCArchive(file)
        else:
            ar = None
        try:
            if ar: 
                ar.extract(file + '_files')
                meta[file]['repack'] = ar.repack_data()
                meta[file]['files'] = ar.list()
                ar.close()
                if not toplevel:
                    os.remove(file)
                    try:
                        os.rename(file + '_files',file)
                    except:
                        time.sleep(0.5) #I have no idea what this does and how it works, except that it fixes something I don't understand
                        os.rename(file + '_files',file)
                else:
                    time.sleep(0.5)
                    os.rename(file, file+'_original')
                    time.sleep(0.5)
                    os.rename(file+'_files', file)
                meta.update(extract(file))
            elif magic == mtex.MAGIC and extract_files:
                meta[file] = { 'type': 'mtex'}
                print('Found a {} at {}'.format(meta[file]['type'], file), file=logfile)
                mtex.mtex_to_image(file, file + '.png', format='PNG') 
                meta[file]['repack'] = mtex.repack_data(file)
                meta[file]['hash'] = config.hashfile(file+'.png')
            #elif magic == gim.MAGIC and extract_files:
            #    meta[file] = { 'type': 'gim' }
            #    gim.gim_to_image(file, file + '.png')
            #    meta[file]['repack'] = gim.repack_data(file)
            elif (magic == ev.MAGIC or (magic&0xFFFF) == ev.MAGIC2) and extract_files:
                meta[file] = { 'type': 'ev'}
                print('Found a {} at {}'.format(meta[file]['type'], file), file=logfile)
                meta[file]['repack'] = ev.dump(file, file+'.txt')
                meta[file]['hash'] = config.hashfile(file+'.txt')
            elif font.isfont(file) and extract_files:
                meta[file] = {'type': 'font'}
                print('Found a {} at {}'.format(meta[file]['type'], file), file=logfile)
                font.codepage(file, file+'.png')
                meta[file]['hash'] = config.hashfile(file+'.png')
            elif ev.isfilevalid(file):
                meta[file] = {'type': 'string'}
                print('Found a {} at {}'.format(meta[file]['type'], file), file=logfile)
                ev.dumpstringfile(file, file+'.txt')
                meta[file]['hash'] = config.hashfile(file+'.txt')
            else:
                pass
        except Exception as e:
            sys.stderr.write('Exception occurred while extracting {}: {}\n'.format(file, e))
    return meta

with open(sys.argv[2], 'wb') as metafile:
    meta = { 'basedir': sys.argv[1] }
    fullextract = len(sys.argv)>3
    with open('logfile.log', 'w') as logfile:
        sys.stdout = logfile
        meta['files'] = extract(sys.argv[1], toplevel=True)
    pickle.dump(meta, metafile)

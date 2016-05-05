# adjustoffsets.py

# safely adjusts the file offsets to fit the modified data.afs into the iso while removing unnecessary padding and accounting for xdelta3 buffer sizes

# usage: adjustoffsets.py offsetsfile sizefile data.afs [xdelta3buffersize=8000000]

from collections import OrderedDict
from os import path
import math
import sys

SECTORSIZE = 0x800
DATASECTORSTART = 29

def main(offsetsfile, sizefile, afsfile, buffersize=8000000):
    # read offsetsfile
    
    bufsize = math.floor(buffersize/SECTORSIZE) if buffersize else 0
    
    with open(offsetsfile, 'r') as f:
        offsets = OrderedDict()
        
        for i in f.readlines():
            offset, name = i.split(',', 1)
            offset = int(offset.strip())
            name = name.strip()
            offsets[name] = offset
            
    with open(sizefile, 'r') as f:
        sizes = {}
        
        for i in f.readlines():
            begin, end, name = i.split(',', 2)
            size = int(end.strip())-int(begin.strip())+1
            name = name.strip()
            sizes[name] = size
            
    afssize = math.ceil(path.getsize(afsfile)/SECTORSIZE)
    sizes[r'\PSP_GAME\USRDIR\data.afs'] = afssize
    
    files = tuple(offsets)
    
    minbufsize = 0
    
    curroffset = DATASECTORSTART
    newoffsets = {}
    for i, file in enumerate(files):
        newoffsets[file] = curroffset
        
        if i == len(files)-1:
            break # can't calculate oldsize for last file

        oldsize = offsets[files[i+1]] - offsets[file] # size including padding
        minsize = sizes[file] # required size
        
        newsize = max(minsize, oldsize-bufsize) if bufsize else minsize # make as small as possible
        reqbufsize = abs(oldsize - newsize)
        if reqbufsize > minbufsize: # check the required actual buffer length
            minbufsize = reqbufsize
        
        curroffset += newsize # bump offset
    
    offsets.update(newoffsets)
    
    if offsetsfile.endswith('.txt'):
        resultfile = offsetsfile[:-4] + '.fixed.txt'
    else:
        resultfile = offsetfile + '.fixed'
    with open(resultfile, 'w') as f:
        f.write(
            '\n'.join(
                str(offsets[i]).zfill(7)+
                ' , '+
                i
                for i in offsets
            )
        )
    
    return minbufsize*SECTORSIZE

if __name__ == "__main__":
    if len(sys.argv) < 4:
        exit('not enough arguments. adjustoffsets.py offsetsfile sizefile afsfile [buffersize=8000000]')
    requiredbuffersize = main(sys.argv[1], sys.argv[2], sys.argv[3], 8000000 if len(sys.argv) < 5 else int(sys.argv[4]))
    print('the required source buffer size is {} Bytes'.format(requiredbuffersize))
    
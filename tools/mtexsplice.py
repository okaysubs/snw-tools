# mtexsplice.def
# alter an Mtexx file to contain the contents of an image
# Usage: mtexdec.py <tex> <img> <outfile>
# Requires the Python Imaging Library.

import sys
import os
from os import path
import struct 
import PIL.Image
import functools
from collections import Counter

USE_PIL_QUANTIZE = False
MAGIC = 0x7865744D
C_SPEEDUP = False
FULL_FULL = 0x1
HALF_FULL = 0x2
HALF_HALF = 0x3

@functools.lru_cache(maxsize=256) #will probably be called many times for the same value
def find_closest_color(colormap, color):
    #colormap and color should be bytes or bytearray's
    if color in colormap:
        return colormap.index(color)
    closest = 0
    distance = 10000000000
    #we'll define distance as |r-r|+|b-b|+|c-c|+3*|a-a|
    if len(color) == 4: #4-byte colors
        for i, colorm in enumerate(colormap):
            dist = (abs(color[0]-colorm[0])+abs(color[1]-colorm[1])+abs(color[2]-colorm[2])+3*abs(color[3]-colorm[3]))
            if dist < distance:
                closest = i
                distance = dist
    else: #2-byte colors: atm unused because I expand the colormap to 4 bytes
        for i, colorm in enumerate(colormap):
            dist = (((abs(color[0])>>4)-(abs(color[0])>>4))+((abs(color[0])&15)-(abs(color[0])&15))+
                ((abs(color[1])>>4)-(abs(color[1])>>4))+3*((abs(color[1])&15)-(abs(color[1])&15)))
            if dist < distance:
                closest = i
                distance = dist
    return closest

mypath = os.path.dirname(os.path.realpath(__file__))
if 'colorfilter.dll' in os.listdir(mypath) and sys.platform.startswith('win'):
    import ctypes
    try:
        ourdll = ctypes.CDLL(path.join(mypath, 'colorfilter.dll'))
        C_SPEEDUP = True
    except:
        pass
def image_into_mtex(mtex, image, dest, create_new_colormap = False):
    with open(mtex, 'rb') as f:
        magic = struct.unpack('<I', f.read(4))[0]
        if magic != MAGIC:
            raise ValueError('Not a Mtex image: {}'.format(magic))

        # we need the header, the data, and the colormap
        # first parse the header to determine what we're dealing with.

         # ????
        f.seek(4, os.SEEK_CUR)
        # File size.
        fsize = struct.unpack('<I', f.read(4))[0]
        # File name.
        fname = (f.read(8) + b'\x00').decode('us-ascii')
        # ????
        f.seek(20, os.SEEK_CUR)
        # Image width and height.
        width, height = struct.unpack('<HH', f.read(4))
        # ????
        f.seek(8, os.SEEK_CUR)
        # Offset to color map.
        cmoffset = struct.unpack('<I', f.read(4))[0]
        # Image data size.
        datalen = struct.unpack('<I', f.read(4))[0]
        # Flags.
        flags = struct.unpack('<I', f.read(4))[0]

        # Image data.
        pixels = f.read(datalen)
        # Seek to color map.
        f.seek(cmoffset)
        # Color map data.
        colormap = f.read()
        # Header data
        f.seek(0)
        header = f.read(64)

        #damn it how do you test what format it is again
        if flags & 0x400 == 0x400:
            format = FULL_FULL
        elif flags & 0x20 == 0x20:
            format = HALF_HALF
        elif flags & 0x40 == 0x40:
            format = HALF_FULL
        else:
            raise ValueError('Unknown image format in {}: {}'.format(source, hex(flags)))

    # extract the pixeldata out of our replacement image
    image = PIL.Image.open(image)

    # sanity check: do we have the proper amount of data
    size = image.width * image.height // (1 if format == FULL_FULL else 2 if format == HALF_FULL else 4)
    assert size == datalen, "Image size mismatch"

    #if image.mode != 'RGBA':
    #    image.convert('RGBA')
    if USE_PIL_QUANTIZE:
       image = image.convert("P", palette = PIL.Image.ADAPTIVE, colors = (256 if format == FULL_FULL else 16))
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    replacement = image.tobytes()
    repl_pixels = [replacement[i:i+4] for i in range(0, len(replacement), 4)]
    repl_size = image.size

    # should check if the image size matches

    #we now have a list of all pixels. create a set of them to see if they conform to the colormap
    if create_new_colormap:
        # print('creating colormap')
        # create a new colormap from the replacement pixels
        if format == FULL_FULL:
            #this should output a 256x4 colormap
            colors = list(set(repl_pixels))
            if len(colors) <= 256:
                colormap = colors + [colors[-1]]*(256-len(colors))
            else:
                # find the 256 most appearing colors
                # count = Counter(repl_pixels)
                # y = count.most_common(256)
                # colormap = [i for i,_ in y]
                colormap = reducecolors(colors, 256)

        elif format == HALF_FULL:
            #this should output a 16x4 colormap
            colors = list(set(repl_pixels))
            if len(colors) <= 16:
                colormap = colors + [colors[-1]]*(16-len(colors))
            else:
                # find the 256 most appearing colors
                # count = Counter(repl_pixels)
                # y = count.most_common(16)
                # colormap = [i for i,_ in y]
                colormap = reducecolors(colors, 16)

        elif format == HALF_HALF:
            #this should output a 16x2 colormap padded with 16x2 0's
            grey = [bytes([i[3], int((i[0]+i[1]+i[2])/3)])for i in repl_pixels] # rgba > aL
            if len(set(grey)) <= 16:
                colormap = grey + [grey[-1]]*(16-len(grey))
            else:
                # count = Counter(grey)
                # y = count.most_common(16)
                # colormap = [i for i,_ in y]
                colormap = reducecolors(grey, 16)

            colormap += [b'\x00\x00']*16

        colormap = b''.join(sorted(colormap))
    # print('converting colormap')
    # we always start with 4-byte colors.
    if format == FULL_FULL or format == HALF_FULL: #if 4-byte colormap
        matchmap = [colormap[i:i+4] for i in range(0, len(colormap), 4)]
    else: #if 2-byte colormap, we'll convert it to 4 byte here. indexes will still be the same
        matchmap = [colormap[i:i+2] for i in range(0, len(colormap), 2)]
        matchmap = [bytes([i[1],i[1],i[1],i[0]]) for i in matchmap]
        matchmap = matchmap[:16]

    if C_SPEEDUP:
        cmaplength = len(matchmap)
        matchmap = [i for i in b''.join(matchmap)]
        matchmap = (ctypes.c_int * (4*cmaplength) )(*matchmap)
        length = len(repl_pixels)
        ccolors = (ctypes.c_int * (4*length) )(*[i for i in b''.join(repl_pixels)])
        function = ourdll.indexiterate
        function.restype = ctypes.POINTER(ctypes.c_int*length)
        indices = function(matchmap, ctypes.c_int(cmaplength), ccolors, ctypes.c_int(length))
        finalindices = [bytes([i]) for i in indices.contents]
    else:
        matchmap = tuple(matchmap)
        # print('calculating indices')
        finalindices = [bytes([find_closest_color(matchmap, i)]) for i in repl_pixels] # very performance intensive.
        # print('building file')

    
    if format == FULL_FULL: #4-byte image
        imagedata = finalindices
    elif format == HALF_FULL or format == HALF_HALF: #2-byte image, concatenate 2 bytes into one
        imagedata = []
        for i in range(0, len(finalindices), 2):
            imagedata.append(bytes([finalindices[i][0]+(finalindices[i+1][0]<<4)]))

    imagedata = b''.join(imagedata)

    with open(dest,'wb') as g:
        g.write(header)
        g.write(imagedata)
        g.write(colormap)

def image_into_image(image, dest, mode=256):
    """shows how the output of the quantization algorithm will look"""
    image = PIL.Image.open(image)
    #if image.mode != 'RGBA':
    #    image.convert('RGBA')
    if USE_PIL_QUANTIZE:
        image = image.convert("P", palette = PIL.Image.ADAPTIVE, colors = (256 if format == FULL_FULL else 16))
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    replacement = image.tobytes()
    repl_pixels = [replacement[i:i+4] for i in range(0, len(replacement), 4)]
    repl_size = image.size

    if mode == 256:
        colors = list(set(repl_pixels))
        if len(colors) <= 256:
            colormap = colors + [colors[-1]]*(256-len(colors))
        else:
            # find the 256 most appearing colors
            # count = Counter(repl_pixels)
            # y = count.most_common(256)
            # colormap = [i for i,_ in y]
            colormap = reducecolors(colors, 256)
    elif mode == 16:
        colors = list(set(repl_pixels))
        if len(colors) <= 16:
            colormap = colors + [colors[-1]]*(16-len(colors))
        else:
            # find the 256 most appearing colors
            # count = Counter(repl_pixels)
            # y = count.most_common(16)
            # colormap = [i for i,_ in y]
            colormap = reducecolors(colors, 16)
    else:
        raise ValueError('ony mode 256 or mode 16 supported')
    #print(sorted(colormap))

    colormap = b''.join(sorted(colormap))
    matchmap = tuple([colormap[i:i+4] for i in range(0, len(colormap), 4)])

    print('calculating indices')
    if C_SPEEDUP:
        cmaplength = len(matchmap)
        cmatchmap = [i for i in b''.join(matchmap)]
        cmatchmap = (ctypes.c_int * (4*cmaplength) )(*cmatchmap)
        length = len(repl_pixels)
        ccolors = (ctypes.c_int * (4*length) )(*[i for i in b''.join(repl_pixels)])
        function = ourdll.indexiterate
        function.restype = ctypes.POINTER(ctypes.c_int*length)
        indices = function(cmatchmap, ctypes.c_int(cmaplength), ccolors, ctypes.c_int(length))
        finalindices = [i for i in indices.contents]
    else:
        matchmap = tuple(matchmap)
        finalindices = [find_closest_color(matchmap, i) for i in repl_pixels] # very performance intensive.
        
    print('building file')

    #ok, got the indices, now calculate back

    newdata = b''.join([matchmap[i] for i in finalindices])
    newimage =  PIL.Image.frombuffer('RGBA', repl_size, newdata, 'raw', 'RGBA', 0, 1)
    newimage.save(dest)


def reducecolors(colors, amount=256):
    #turn bytes into arrays
    if len(colors) < amount:
        raise ValueError('can\'t quantize into higher amount')
    
    if len(colors[0]) == 4:
        lencolors = 4
    else:
        lencolors = 2

    newcolors = []
    for i in colors:
        if lencolors == 4:
            newcolors.append([i[0], i[1], i[2], i[3]])
        else:
            newcolors.append([i[0], i[1]])
    
    if amount == 256:
        orderedcolors = quantize256(newcolors)
    else:
        orderedcolors = quantize16(newcolors)
    
    if lencolors == 4:
        return [bytes(average4(i, j, amount)) for j, i in enumerate(orderedcolors)]
    else:
        return [bytes(average2(i, j)) for j, i in enumerate(orderedcolors)]

def quantize256(colors):
    colors1 = quantize16(colors)
    colors2 = []
    for color in colors1:
        colors2.extend(quantize16(color))

    return colors2 # 256 color values

def quantize16(colors):
    a, b = sort(colors, 0)

    c, d = sort(a, 1)
    e, f = sort(b, 1)

    h, i = sort(c, 2)
    j, k = sort(d, 2)
    l, m = sort(e, 2)
    n, o = sort(f, 2)

    return (sort(h, 3) + sort(i, 3) + sort(j, 3) + sort(k, 3) +
            sort(l, 3) + sort(m, 3) + sort(n, 3) + sort(o, 3))

def sort(array, index):
    a = sorted(array, key = lambda x: x[index])
    return [a[:len(a)//2],a[len(a)//2:]]
def average4(colors, index, amount):
    COLORDIST = COLORDIST256 if amount==256 else COLORDIST16f
    av =  [avg(red(colors),COLORDIST[index][0]), 
        avg(green(colors),COLORDIST[index][1]), 
        avg(blue(colors),COLORDIST[index][2]), 
        avg(alpha(colors),COLORDIST[index][3])]
    return min(colors, key = lambda x: ((x[0]-av[0])**2+(x[1]-av[1])**2+(x[2]-av[2])**2+3*(x[3]-av[3])**2))
def average2(colors, index):
    av =  [avg(red(colors),COLORDIST16h[index][0],2), avg(green(colors),COLORDIST16h[index][1],2)]
    return min(colors, key = lambda x: ((x[0]-av[0])**2+(x[1]-av[1])**2))
def avg(values, whereto, wheretorange=4):
    if wheretorange == 4 and (whereto == 1 or whereto == 2):
        return round(sum(values)/len(values))
    elif (wheretorange == 4 and whereto == 3) or (wheretorange == 2 and whereto == 1):
        return (max(values))
    elif whereto == 0:
        return (min(values))
    #return round(sum(values)/len(values))
def red(colors):
    return [i[0] for i in colors]
def green(colors):
    return [i[1] for i in colors]
def blue(colors):
    return [i[2] for i in colors]
def alpha(colors):
    return [i[3] for i in colors]

COLORDIST256 = [
[0,0,0,0],[0,0,0,1],[0,0,1,0],[0,0,1,1],[0,1,0,0],[0,1,0,
1],[0,1,1,0],[0,1,1,1],[1,0,0,0],[1,0,0,1],[1,0,1,0],[1,0,
1,1],[1,1,0,0],[1,1,0,1],[1,1,1,0],[1,1,1,1],[0,0,0,2],[
0,0,0,3],[0,0,1,2],[0,0,1,3],[0,1,0,2],[0,1,0,3],[0,1,1,2
],[0,1,1,3],[1,0,0,2],[1,0,0,3],[1,0,1,2],[1,0,1,3],[1,1,
0,2],[1,1,0,3],[1,1,1,2],[1,1,1,3],[0,0,2,0],[0,0,2,1],[0,
0,3,0],[0,0,3,1],[0,1,2,0],[0,1,2,1],[0,1,3,0],[0,1,3,1],
[1,0,2,0],[1,0,2,1],[1,0,3,0],[1,0,3,1],[1,1,2,0],[1,1,2,
1],[1,1,3,0],[1,1,3,1],[0,0,2,2],[0,0,2,3],[0,0,3,2],[0,0,
3,3],[0,1,2,2],[0,1,2,3],[0,1,3,2],[0,1,3,3],[1,0,2,2],[
1,0,2,3],[1,0,3,2],[1,0,3,3],[1,1,2,2],[1,1,2,3],[1,1,3,2
],[1,1,3,3],[0,2,0,0],[0,2,0,1],[0,2,1,0],[0,2,1,1],[0,3,
0,0],[0,3,0,1],[0,3,1,0],[0,3,1,1],[1,2,0,0],[1,2,0,1],[1,
2,1,0],[1,2,1,1],[1,3,0,0],[1,3,0,1],[1,3,1,0],[1,3,1,1],
[0,2,0,2],[0,2,0,3],[0,2,1,2],[0,2,1,3],[0,3,0,2],[0,3,0,
3],[0,3,1,2],[0,3,1,3],[1,2,0,2],[1,2,0,3],[1,2,1,2],[1,2,
1,3],[1,3,0,2],[1,3,0,3],[1,3,1,2],[1,3,1,3],[0,2,2,0],[
0,2,2,1],[0,2,3,0],[0,2,3,1],[0,3,2,0],[0,3,2,1],[0,3,3,0
],[0,3,3,1],[1,2,2,0],[1,2,2,1],[1,2,3,0],[1,2,3,1],[1,3,
2,0],[1,3,2,1],[1,3,3,0],[1,3,3,1],[0,2,2,2],[0,2,2,3],[0,
2,3,2],[0,2,3,3],[0,3,2,2],[0,3,2,3],[0,3,3,2],[0,3,3,3],
[1,2,2,2],[1,2,2,3],[1,2,3,2],[1,2,3,3],[1,3,2,2],[1,3,2,
3],[1,3,3,2],[1,3,3,3],[2,0,0,0],[2,0,0,1],[2,0,1,0],[2,0,
1,1],[2,1,0,0],[2,1,0,1],[2,1,1,0],[2,1,1,1],[3,0,0,0],[
3,0,0,1],[3,0,1,0],[3,0,1,1],[3,1,0,0],[3,1,0,1],[3,1,1,0
],[3,1,1,1],[2,0,0,2],[2,0,0,3],[2,0,1,2],[2,0,1,3],[2,1,
0,2],[2,1,0,3],[2,1,1,2],[2,1,1,3],[3,0,0,2],[3,0,0,3],[3,
0,1,2],[3,0,1,3],[3,1,0,2],[3,1,0,3],[3,1,1,2],[3,1,1,3],
[2,0,2,0],[2,0,2,1],[2,0,3,0],[2,0,3,1],[2,1,2,0],[2,1,2,
1],[2,1,3,0],[2,1,3,1],[3,0,2,0],[3,0,2,1],[3,0,3,0],[3,0,
3,1],[3,1,2,0],[3,1,2,1],[3,1,3,0],[3,1,3,1],[2,0,2,2],[
2,0,2,3],[2,0,3,2],[2,0,3,3],[2,1,2,2],[2,1,2,3],[2,1,3,2
],[2,1,3,3],[3,0,2,2],[3,0,2,3],[3,0,3,2],[3,0,3,3],[3,1,
2,2],[3,1,2,3],[3,1,3,2],[3,1,3,3],[2,2,0,0],[2,2,0,1],[2,
2,1,0],[2,2,1,1],[2,3,0,0],[2,3,0,1],[2,3,1,0],[2,3,1,1],
[3,2,0,0],[3,2,0,1],[3,2,1,0],[3,2,1,1],[3,3,0,0],[3,3,0,
1],[3,3,1,0],[3,3,1,1],[2,2,0,2],[2,2,0,3],[2,2,1,2],[2,2,
1,3],[2,3,0,2],[2,3,0,3],[2,3,1,2],[2,3,1,3],[3,2,0,2],[
3,2,0,3],[3,2,1,2],[3,2,1,3],[3,3,0,2],[3,3,0,3],[3,3,1,2
],[3,3,1,3],[2,2,2,0],[2,2,2,1],[2,2,3,0],[2,2,3,1],[2,3,
2,0],[2,3,2,1],[2,3,3,0],[2,3,3,1],[3,2,2,0],[3,2,2,1],[3,
2,3,0],[3,2,3,1],[3,3,2,0],[3,3,2,1],[3,3,3,0],[3,3,3,1],
[2,2,2,2],[2,2,2,3],[2,2,3,2],[2,2,3,3],[2,3,2,2],[2,3,2,
3],[2,3,3,2],[2,3,3,3],[3,2,2,2],[3,2,2,3],[3,2,3,2],[3,2,
3,3],[3,3,2,2],[3,3,2,3],[3,3,3,2],[3,3,3,3]]
COLORDIST16f = [
[0,0,0,0],[0,0,0,1],[0,0,1,0],[0,0,1,1],[0,1,0,0],[0,1,0,
1],[0,1,1,0],[0,1,1,1],[1,0,0,0],[1,0,0,1],[1,0,1,0],[1,0,
1,1],[1,1,0,0],[1,1,0,1],[1,1,1,0],[1,1,1,1]]
COLORDIST16h = [
[0,0],[1,0],[0,1],[1,1],[0,2],[1,2],[0,3],[1,3],[2,0],[3,0],
[2,1],[3,1],[2,2],[3,2],[2,3],[3,3]]


if __name__ == "__main__":
    if len(sys.argv) < 4:
        exit('usage: {} tex img dest <create_new_colormap>'.format(sys.argv[0]))
    else:
        image_into_mtex(sys.argv[1], sys.argv[2], sys.argv[3], len(sys.argv) > 4)



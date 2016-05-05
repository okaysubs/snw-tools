# font.py
# edit the font files
import PIL.Image
import sys


# dump and make just generate images, codepage and uncodepage make actual pretty codepages

MAGIC = 0x00000000
HALFMAP = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?\''

def isfont(file):
    with open(file, 'rb') as f:
        data = f.read(64)
    if len(data) != 64:
        return False
    if data[0:4] != b'\x00\x00\x00\x00':
        return False
    color = data[4:7]
    if color == b'\x00\x00\x00':
        return False
    for i in range(2,16):
        if color != data[4*i:4*i+3]:
            return False
    return True


def dump(file, dest, to_black_white=True):
    with open(file, 'rb') as f:
        colormap = []
        for j in range(16):
            colormap.append(f.read(4))
        image = f.read()
    indices = []

    for i in image:
        indices.extend([i&15,i>>4])

    if to_black_white:
        for i in range(len(colormap)):
            colormap[i] = [(colormap[i][0]*colormap[i][3])//255,
                           (colormap[i][1]*colormap[i][3])//255,
                           (colormap[i][2]*colormap[i][3])//255,
                           255]

    pixels = b''.join([bytes(colormap[i]) for i in indices])

    width = 32
    height = len(indices)//width
    img = PIL.Image.frombytes('RGBA', (width, height), pixels)
    img.save(dest)

def widthhax(file, halfwidthfile, dest, chars = HALFMAP, to_black_white = True):
    #bunch of copy-pasted code follows for the original file
    with open(file, 'rb') as f:
        colormap = []
        for j in range(16):
            colormap.append(f.read(4))
        image = f.read()
    indices = []

    for i in image:
        indices.extend([i&15,i>>4])

    if to_black_white:
        for i in range(len(colormap)):
            colormap[i] = [(colormap[i][0]*colormap[i][3])//255,
                           (colormap[i][1]*colormap[i][3])//255,
                           (colormap[i][2]*colormap[i][3])//255,
                           255]
    pixels = b''.join([bytes(colormap[i]) for i in indices])

    width = 32
    height = len(indices)//width
    imagewidth = 2
    imageheight = height//16
    img = PIL.Image.frombytes('RGBA', (width, height), pixels)
    letters = []
    for i in range(imagewidth*imageheight):
        letters.append(img.crop((16*(i%2),
                                   16*(i//2),
                                   16*(i%2)+16,
                                   16*(i//2)+16
                                   )))
    #bunch of copy-pasted code for the file to add:
    with open(halfwidthfile, 'rb') as f:
        rcolormap = []
        for j in range(16):
            rcolormap.append(f.read(4))
        rimage = f.read()
    rindices = []

    for i in rimage:
        rindices.extend([i&15,i>>4])

    if to_black_white:
        for i in range(len(rcolormap)):
            rcolormap[i] = [(rcolormap[i][0]*rcolormap[i][3])//255,
                           (rcolormap[i][1]*rcolormap[i][3])//255,
                           (rcolormap[i][2]*rcolormap[i][3])//255,
                           255]
    rpixels = b''.join([bytes(rcolormap[i]) for i in rindices])

    rwidth = 32
    rheight = len(rindices)//rwidth
    rimagewidth = 2
    rimageheight = rheight//16
    rimg = PIL.Image.frombytes('RGBA', (rwidth, rheight), rpixels)
    rletters = []
    for i in range(rimagewidth*rimageheight):
        rletters.append(rimg.crop((16*(i%2),
                                   16*(i//2),
                                   16*(i%2)+8, #attention. only 8 width
                                   16*(i//2)+16
                                   )))
    #we now have the original characters stored in letters, and the left portion of half-width stored in rletters
    for i in chars:
        for j in chars:
            tempimg = PIL.Image.new('RGBA', (16, 16), (255,0,0,255))
            tempimg.paste(rletters[ord(i)-32], (0, 0))
            tempimg.paste(rletters[ord(j)-32], (8, 0))
            letters.append(tempimg)
    for i in range(16-((len(chars)**2)%16)):
        letters.append(PIL.Image.new('RGBA', (16, 16), (0,0,0,255)))
    #more copy-pasted code. I should refactor this file probably
    new_imgs = [PIL.Image.new('RGBA',(17*16, 17*16), (255,0,0,255)) for i in range(len(letters)//256 + (1 if len(letters)%256 != 0 else 0))]
    for i, subimg in enumerate(letters):
        new_imgs[i//256].paste(subimg, (17*((i%256)%16),17*((i%256)//16)))

    final_img = PIL.Image.new('RGBA', (17*16, 18*16*len(new_imgs)), (255,0,0,255))
    for i, subimg in enumerate(new_imgs):
        final_img.paste(subimg, (0, 18*16*i))

    final_img.save(dest)

def codepage(file, dest, to_black_white=True):
    with open(file, 'rb') as f:
        colormap = []
        for j in range(16):
            colormap.append(f.read(4))
        image = f.read()
    indices = []

    for i in image:
        indices.extend([i&15,i>>4])

    if to_black_white:
        for i in range(len(colormap)):
            colormap[i] = [(colormap[i][0]*colormap[i][3])//255,
                           (colormap[i][1]*colormap[i][3])//255,
                           (colormap[i][2]*colormap[i][3])//255,
                           255]
    pixels = b''.join([bytes(colormap[i]) for i in indices])

    width = 32
    height = len(indices)//width
    imagewidth = 2
    imageheight = height//16
    img = PIL.Image.frombytes('RGBA', (width, height), pixels)
    letters = []
    for i in range(imagewidth*imageheight):
        letters.append(img.crop((16*(i%2),
                                   16*(i//2),
                                   16*(i%2)+16,
                                   16*(i//2)+16
                                   )))
    new_imgs = [PIL.Image.new('RGBA',(17*16, 17*16), (255,0,0,255)) for i in range(len(letters)//256 + (1 if len(letters)%256 != 0 else 0))]
    for i, subimg in enumerate(letters):
        new_imgs[i//256].paste(subimg, (17*((i%256)%16),17*((i%256)//16)))

    final_img = PIL.Image.new('RGBA', (17*16, 18*16*len(new_imgs)), (255,0,0,255))
    for i, subimg in enumerate(new_imgs):
        final_img.paste(subimg, (0, 18*16*i))

    final_img.save(dest)

def uncodepage(file, dest, from_black_white=True, color=b'\xff\xff\xff', colormapfile = None):
    cimg = PIL.Image.open(file)
    if cimg.mode != 'RGBA':
        cimg.convert('RGBA')
    #black magic goes here.
    #the subimages are 17x*16x17*16 blocks
    #the subsubimages are 16x16, one pixel apart
    totalwidth, totalheight = cimg.size
    if totalwidth != 16*17 or totalheight%(16*18) != 0: 
        raise ValueError('not the right image size, width should be 16*17 by n*16*18')
    new_img_count = totalheight//(18*16)
    new_imgs = [cimg.crop((0, 16*18*i, 16*17, 16*18*i+16*17)) for i in range(new_img_count)]
    chars = []
    for subimg in new_imgs:
        for i in range(256):
            newchar = subimg.crop((17*(i%16),17*(i//16),17*(i%16)+16,17*(i//16)+16))
            if newchar.getpixel((0,0)) == (255,0,0,255):
                break
            chars.append(newchar)
    img = PIL.Image.new('RGBA', (32, 16*len(chars)//2), (255,0,0,255))
    for i, char in enumerate(chars):
        img.paste(char, (16*(i%2), 16*(i//2)))

    #finished with reconstructing here
    pixels = img.tobytes()
    
    if not colormapfile or True: #option disabled until further notice
        colormap = [b'\x00\x00\x00\x00']
        for i in range(1,16):
            colormap.append(color+bytes([(i<<4)+i]))
    else:
        with open(colormapfile, 'rb') as g:
            colormap = []
            for j in range(16):
                colormap.append(g.read(4))

    pixels = [[pixels[i],pixels[i+1],pixels[i+2],pixels[i+3]] for i in range(0,len(pixels),4)]
    if from_black_white:
        indices = [((i[0]+i[1]+i[2])//3)>>4 for i in pixels]
    else:
        indices = [(i[3])>>4 for i in pixels]

    data = []
    for i in range(0, len(indices), 2):
        data.append((indices[i+1]<<4)+indices[i])

    with open(dest, 'wb') as f:
        f.write(b''.join(colormap))
        f.write(bytes(data))

def make(file, dest, from_black_white=True, color=b'\xff\xff\xff', colormapfile = None):
    img = PIL.Image.open(file)
    if img.mode != 'RGBA':
        img.convert('RGBA')
    pixels = img.tobytes()
    
    if not colormapfile or True: #option disabled until further notice
        colormap = [b'\x00\x00\x00\x00']
        for i in range(1,16):
            colormap.append(color+bytes([(i<<4)+i]))
    else:
        with open(colormapfile, 'rb') as g:
            colormap = []
            for j in range(16):
                colormap.append(g.read(4))

    pixels = [[pixels[i],pixels[i+1],pixels[i+2],pixels[i+3]] for i in range(0,len(pixels),4)]
    if from_black_white:
        indices = [((i[0]+i[1]+i[2])//3)>>4 for i in pixels]
    else:
        indices = [(i[3])>>4 for i in pixels]

    data = []
    for i in range(0, len(indices), 2):
        data.append((indices[i+1]<<4)+indices[i])

    with open(dest, 'wb') as f:
        f.write(b''.join(colormap))
        f.write(bytes(data))
        
if __name__ == "__main__":
    if len(sys.argv)<4:
        exit('usage {} load|save file dest')

    if sys.argv[1] == "load":
        dump(sys.argv[2],sys.argv[3])
    else:
        make(sys.argv[2],sys.argv[3])



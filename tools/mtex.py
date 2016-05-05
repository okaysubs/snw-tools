import sys
import os
import struct
import binascii
import PIL.Image

MAGIC = 0x7865744D

FORMAT_FULL = 1
FORMAT_HALFPIXEL = 2
FORMAT_HALF = 3

COLORMAPSIZE = {
    FORMAT_FULL: 0x100,
    FORMAT_HALFPIXEL: 0x10,
    FORMAT_HALF: 0x10
}
COLORSIZE = {
    FORMAT_FULL: 0x4,
    FORMAT_HALFPIXEL: 0x4,
    FORMAT_HALF: 0x2
}

def mtex_to_image(source, dest=None, format='GIF'):
    with open(source, 'rb') as f:
        magic = struct.unpack('<I', f.read(4))[0]
        if magic != MAGIC:
            raise ValueError('Not a Mtex image: {}'.format(magic))

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

        if flags & 0x400 == 0x400:
            iformat = FORMAT_FULL
        elif flags & 0x20 == 0x20:
            iformat = FORMAT_HALF
        elif flags & 0x40 == 0x40:
            iformat = FORMAT_HALFPIXEL
        else:
            raise ValueError('Unknown image format in {}: {}'.format(source, hex(flags)))

        # Image data.
        pixels = f.read(datalen)
        # Seek to color map.
        f.seek(cmoffset)
        # Color map data.
        colormap = f.read(COLORMAPSIZE[iformat] * COLORSIZE[iformat])

        # Build pixel data.
        imagedata = []
        if iformat == FORMAT_FULL:
            width = int(datalen / height)
            for byte in pixels:
                cmoffset = byte * 4
                color = colormap[cmoffset:cmoffset + 4]
                imagedata.append(color)
        elif iformat == FORMAT_HALFPIXEL:
            width = int(datalen * 2 / height)
            for byte in pixels:
                byte1, byte2 = byte >> 4, byte & 0xF
                cmoffset1 = byte1 * 4
                color1 = colormap[cmoffset1:cmoffset1 + 4]
                cmoffset2 = byte2 * 4
                color2 = colormap[cmoffset2:cmoffset2 + 4]
                imagedata.extend([color2, color1])
        elif iformat == FORMAT_HALF:
            width = int(datalen * 2 / height)

            def gray2rgba(gray):
                hex = gray[1]
                alpha = gray[0]
                return bytes([hex, hex, hex, alpha])

            for byte in pixels:
                byte1, byte2 = byte >> 4, byte & 0xF
                cmoffset1 = byte1 * 2
                cmoffset2 = byte2 * 2
                color1 = gray2rgba(colormap[cmoffset1:cmoffset1 + 2])
                color2 = gray2rgba(colormap[cmoffset2:cmoffset2 + 2])
                imagedata.extend([color2, color1])

        pixeldata = b''.join(imagedata)

        # Save image.
        if dest is None:
            dest = fname.lstrip('/').replace('.tex', format.lower())
        image = PIL.Image.frombuffer('RGBA', (width, height), pixeldata, 'raw', 'RGBA', 0, 1)
        image.save(dest, format)

def repack_data(file):
    with open(file, 'rb') as f:
        return f.read()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        exit('usage: {} SRC DEST [FORMAT]'.format(sys.argv[0]))

    mtex_to_image(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'GIF')

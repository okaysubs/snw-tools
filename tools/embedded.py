# embedded.py
# extracts the embedded MARC archive within the EBOOT.BIN executable of the sora no woto vn and repacks it

import struct
import sys

def getmarcdata(data):
    start = data.index(b"MARC")
    fcount, = struct.unpack("<I", data[start + 4 : start + 8])
    length, = struct.unpack("<I", data[start + fcount * 4 + 8 : start + fcount * 4 + 12])
    return start, length

def extract(binary, outfile):
    with open(binary, "rb") as f:
        data = f.read()

    start, length = getmarcdata(data)

    with open(outfile, "wb") as f:
        f.write(data[start : start + length])

def repack(binary, replacement):
    with open(binary, "rb") as f:
        data = f.read()

    start, length = getmarcdata(data)

    with open(replacement, "rb") as f:
        repl = f.read()

    if len(repl) != length:
        raise ValueError("Replacement archive length does not match up")

    data = bytearray(data)
    data[start : start + length] = repl

    with open(binary, "wb") as f:
        f.write(data)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        exit("usage: {} extract|repack <eboot.bin> <embedded.marc>".format(sys.argv[0]))

    if sys.argv[1] == "extract":
        extract(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "repack":
        repack(sys.argv[2], sys.argv[3])
    else:
        exit("usage: {} extract|repack <eboot.bin> <embedded.marc>".format(sys.argv[0]))

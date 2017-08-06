import PIL.Image, PIL.ImageOps
import sys

widths = [
  # [ ]  !   "   #   $   %   &   '   (   )   *   +   ,   -   .   /
     8,  9, 14, 18, 14, 22, 19,  8, 12, 12, 15, 17,  8, 15,  8, 15,
  #  0   1   2   3   4   5   6   7   8   9   :   ;   <   =   >   ?
    17, 12, 16, 16, 17, 15, 16, 17, 15, 16,  8,  8, 17, 17, 17, 14,
  #  @   A   B   C   D   E   F   G   H   I   J   K   L   M   N   O
    19, 20, 19, 19, 20, 17, 17, 19, 19,  8, 11, 21, 16, 24, 20, 21,
  #  P   Q   R   S   T   U   V   W   X   Y   Z   [   \   ]   ^   _
    19, 22, 19, 15, 17, 19, 20, 28, 18, 18, 17, 13, 15, 13, 15, 19,
  #  `   a   b   c   d   e   f   g   h   i   j   k   l   m   n   o
    11, 18, 18, 17, 17, 17, 13, 17, 18,  8,  8, 17, 11, 26, 17, 18,
  #  p   q   r   s   t   u   v   w   x   y   z   {   |   }   ~   
    18, 18, 13, 13, 12, 17, 17, 27, 17, 17, 15, 12,  7, 12, 16, 17,
]

overrides = {
    # special mentions go out to a trailing J or T as they tend to always look out of place
    # as these characters are almost never used trailing we don't care that much though.
    "Ta": 14,
    "Tc": 14,
    "Td": 14,
    "Te": 14,
    "Tg": 14,
    "To": 14,
    "Tq": 14,
    "Tu": 16,
    "Tv": 16,
    "Ty": 16,
    "T.": 14,
    "T,": 14,
    "TA": 14,

#    "LT": 12,
    "LY": 12,
    "L'": 12,
    "L\"": 12,
#    "L`": 12,

    "YA": 14,
    "Ya": 16,
    "Yc": 16,
    "Yd": 16,
    "Ye": 16,
    "Yg": 16,
    "Y.": 14,
    "Y,": 14,

    "FA": 15,
    "F,": 13,
    "F.": 13,

    "f,": 11,
    "f.": 11,
    "fa": 11,
    "fc": 11,
    "fd": 11,
    "fe": 11,
    "fo": 11,
    "fr": 11,

#    "AJ": 16,
    "AT": 16,
    "A'": 18,
    "A\"": 18,
#    "A`": 16,

    "B'": 17,
    "B\"": 17,
#    "B`": 17,

    "r,": 9,
    "r.": 9,

    "'A": 6,
    "'J": 4,
    "'.": 4,
    "',": 4,

#    "`A": 9,
#    "`J": 7,
#    "`.": 7,
#    "`,": 7,

    "\"A": 12,
    "\"J": 10,
    "\".": 10,
    "\",": 10,

    ".'": 4,
#    ".`": 4,
    ".\"": 4,

    ",'": 4,
#    ",`": 4,
    ",\"": 4,
}

relevant = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'`\",.?"

def main():
    if len(sys.argv) < 3:
        exit("Format: {} [test|build] args".format(sys.argv[0]))

    if sys.argv[1] == "test":
        test()
    elif sys.argv[1] == "build":
        build()
    else:
        exit("Invalid command specified. Expected test or build.")

def test():
    infile = sys.argv[2]

    img = PIL.Image.open(infile)
    if img.mode != 'RGBA':
        img.convert('RGBA')

    chunks = []
    for y in range(6):
        for x in range(16):
            chunks.append(img.crop((x*17, y*17, x*17 + 16, y*17 + 16)))

    chunks = [c.resize((32, 32), PIL.Image.NEAREST) for c in chunks]

    while True:
        leading = input(">>> ");
        if not leading:
            continue
        if len(leading) != 1:
            try:
                combi, val = leading.split()
                val = int(val)
                overrides[combi] = val
                continue
            except Exception as e:
                print(e)
                continue

        result = PIL.Image.new('RGBA', (64, len(relevant)*32))
        for i, trailing in enumerate(relevant):
            combi = leading + trailing
            lindex = ord(leading) - 32
            tindex = ord(trailing) - 32
            if combi in overrides:
                spacing = overrides[combi]
            else:
                spacing = widths[lindex]

            temp = PIL.Image.new('RGBA', (64, 32))
            temp.paste(chunks[lindex], (0, 0))

            temp2 = PIL.Image.new('L', (64, 32))
            temp2.paste(chunks[tindex], (spacing, 0))
            temp2 = PIL.ImageOps.invert(temp2)

            white = PIL.Image.new('RGBA', (64, 32), (255, 255, 255, 255))
            temp = PIL.Image.composite(temp, white, temp2)

            result.paste(temp, (0, i * 32))
        result.show()

def build():
    o = [(ord(key[1]) << 8 | ord(key[0]), key, value) for key, value in overrides.items()]
    o.sort()
    for (actkey, key, value) in o:
        print(".halfword {}, {} ; {}".format(hex(actkey), value, key))

if __name__ == '__main__':
    main()
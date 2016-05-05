REPLACEMENT_RANGES = [
    ((0x8100, 0x811F), 0x025F), #0x835F - 0x837E
    ((0x8130, 0x8139), 0x011F), #0x824F - 0x8258
    ((0x813A, 0x813F), 0x0246), #0x8300 - 0x8385
    ((0x8141, 0x815A), 0x011F), #0x8260 - 0x8279
    ((0x815B, 0x815F), 0x022B), #0x8386 - 0x838A
    ((0x8161, 0x817A), 0x0120), #0x8281 - 0x829A
    ((0x817B, 0x817F), 0x0210), #0x838B - 0x838F
    ((0x8181, 0x81D3), 0x011E), #0x829E - 0x82F1
    ((0x81D4, 0x81DA), 0x01BC), #0x8390 - 0x8393
    ((0x81DD, 0x81E0),-0x0035), #0x81A6 - 0x81AB
    ((0x81E1, 0x81FF), 0x015F), #0x8340 - 0x835E
    ((0x8201, 0x825E), 0x069E), #0x889F - 0x88FC
    ((0x8DFE, 0x8E09),-0x06BE), #0x8740 - 0x874B #numbers
]
REVERSE_RANGES = [ ((lower + offset, upper + offset), -offset) for (lower, upper), offset in REPLACEMENT_RANGES]

REPLACEMENT_SINGLES = {
    0x8120: 0x8140,
    0x8121: 0x8149,
    0x8122: 0x8168,
    0x8123: 0x8194,
    0x8124: 0x8163,
    0x8125: 0x8193,
    0x8126: 0x8195,
    0x8127: 0x8158,
    0x8128: 0x8169,
    0x8129: 0x816A,
    0x812A: 0x8196,
    0x812B: 0x817B,
    0x812C: 0x8141,
    0x812D: 0x817C,
    0x812E: 0x8142,
    0x812F: 0x815E,
    0x8140: 0x81F4,
    0x8160: 0x8148,
    0x8180: 0x8145,
    0x81DB: 0x8175,
    0x81DC: 0x8176,

    0x8200: 0x8160,
    0x825F: 0x815B, #5B or 5C? also general unknown replacement char

    0x8DD4: 0x8198, #trademark, translated as section sign.
    0x8DD5: 0x8151, #underscore?
    0x8DD6: 0x8167, #closingquote
    0x8DD7: 0x8177, #doubleopenquote
    0x8DD8: 0x8178, #doubleclosingquote
    0x8DD9: 0x81F3, #musical half note lower

    0x8DDA: 0x997A,
    0x8DDB: 0x99DA,
    0x8DDC: 0x9A68,
    0x8DDD: 0x9A6B,
    0x8DDE: 0x9ABD,
    0x8DDF: 0x9AF8,
    0x8DE0: 0x9B77,
    0x8DE1: 0x9B5A,
    0x8DE2: 0x9BA0,
    0x8DE3: 0x9D86,
    0x8DE4: 0x9E58,
    0x8DE5: 0x9FAD,
    0x8DE6: 0xE0D6,
    0x8DE7: 0xE0F8,
    0x8DE8: 0xE165,
    0x8DE9: 0xE175,
    0x8DEA: 0xE1C5,
    0x8DEB: 0xE253,
    0x8DEC: 0xE2C4,
    0x8DED: 0xE34A,
    0x8DEE: 0xE472,
    0x8DEF: 0xE6D2,
    0x8DF0: 0xE74F,
    0x8DF1: 0xE753,
    0x8DF2: 0xE7AF,

    0x8DF8: 0x9F4E,
    0x8DF9: 0xE056,
    0x8DFA: 0xE07E,
    0x8DFB: 0xE1C1,
    0x8DFC: 0xE256,
    0x8DFD: 0x96F7,

    0x8DF3: 0x8144, #dot
    0x8DF4: 0x8146, #colon
    0x8DF5: 0x8166, #signle quote
    0x8DF6: 0x8199, #star
    0x8DF7: 0x81FC, #circle

    0x8E0A: 0x99CC,
    0x8E0B: 0x9AA2,
    0x8E0C: 0x8C62,
    0x8E0D: 0xE359,
    0x8E0E: 0xE3A9,
    0x8E0F: 0xE4BB,

    0x8E10: 0xE748,
    0x8E11: 0xE7B3,
    0x8E12: 0x96F6,
}
REVERSE_SINGLES = { v: k for k, v in REPLACEMENT_SINGLES.items() }

# Half-width hackery.
HALFMAP = [ord(i) for i in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?\'']
# Multi-byte sequence bounds.
SEQUENCE_BOUNDS = (0x81, 0x91)


def to_jis(byte):
    # Non-standard positions.
    if byte in REPLACEMENT_SINGLES:
        return REPLACEMENT_SINGLES[byte]

    # Non-standard ranges.
    for (lower, upper), offset in REPLACEMENT_RANGES:
        if lower <= byte <= upper:
            return offset + byte

    # Multibyte things.
    if 0x8260 <= byte <= 0x8E12:
        pos = byte - 0x8260
        div, rem = divmod(pos, 0xC0)
        base = ((div + 0x89) << 8) | (rem + 0x40)
        if rem <= 0x3F:
            return base - 1
        if rem <= 0x5E:
            return base
        return base - 2

    # Half-width things.
    if 0x8E20 <= byte <= 0x8E20 + len(HALFMAP) ** 2:
        pos = byte - 0x8E20
        div, rem = divmod(pos, len(HALFMAP))
        return (HALFMAP[div] << 8) | HALFMAP[rem]

    # Assume full-width space.
    return 0x8140

def from_jis(char):
    # Transform space.
    if char == 0x8140:
        return 0x8120

    # Non-standard positions.
    if char in REVERSE_SINGLES:
        return REVERSE_SINGLES[char]

    # Non-standard ranges:
    for (lower, upper), offset in REVERSE_RANGES:
        if lower <= char <= upper:
            return char + offset

    # Multibyte things.
    if 0x8940 <= char <= 0x9FFC:
        pos = char - 0x8900
        div, rem = pos >> 8, pos & 0xFF
        base = (0x8260 + div * 0xC0) | (rem - 0x40)
        if rem <= 0x7E:
            return base + 1
        if rem <= 0x9E:
            return base
        return base + 2

    # Half-width things.
    if 0x2020 <= char <= 0x7F7F:
        div, rem = char >> 8, char & 0xFF
        base = 0x8E20
        return base + len(HALFMAP) * HALFMAP.index(div) + HALFMAP.index(rem)

    raise ValueError('Invalid pseudo-SJIS code point: {}'.format(char))

def decode(encoded):
    first = None
    res = bytearray()

    for byte in encoded:
        if first:
            # Second byte of multi-byte sequence.
            chars = to_jis((first << 8) | byte)
            first = None
            # Single-byte result, prepend \.
            if chars < 0x8000:
                res.append(b'\\')
            res.extend([chars >> 8, chars & 0xFF])
            continue

        if SEQUENCE_BOUNDS[0] <= byte <= SEQUENCE_BOUNDS[1]:
            # First byte of multi-byte sequence.
            first = byte
            continue

        # Regular byte.
        res.append(byte)

    # Neither pure SJIS nor the X.0213 variant have exactly what we need:
    #  Pure misses bubble numbers (⑨)
    #  X.0213 has incorrect multi-byte entries.
    try:
        return res.decode('shift_jis')
    except UnicodeDecodeError:
        return res.decode('shift_jisx0213')

def encode(input):
    first = None
    escape = False
    res = bytearray()

    try:
        input = input.encode('shift_jis')
    except UnicodeDecodeError:
        input = input.encode('shift_jisx0213')

    for byte in input:
        if first:
            # Second part of multi-byte sequence.
            chars = from_jis((first << 8) | byte)
            first = None
            res.extend([chars >> 8, chars & 0xFF])
            continue

        if byte == '\\':
            # Escaped single-byte result.
            escape = True
            continue

        # First byte of multi-byte sequence, or escaped single-byte.
        if 0x81 <= byte <= 0x9F or 0xE0 <= byte <= 0xFC or escape:
            first = byte
            escape = False
            continue

        # Regular byte.
        res.append(byte)

    return res

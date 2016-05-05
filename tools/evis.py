import sys
import struct
import encvis

MAGIC = b'\x10\x04\x08\x00'
PADDING = b'\xff\xff'

CMD_DIALOGUE = b'\xfe\xff'
CMD_CHOICE = b'\xfc\xff'

CMD_SLEEP = b'\x05\x00'

CMD_JUMP = b'\x04\x00'
CMD_CONDJUMP = b'\x03\x00'
CMD_LEVELJUMP = b'\x1f\x04'
CMD_PERFJUMP = b'\x36\x04'
CMD_CHOICEJUMP = b'\x07\x04'

CMD_SPRITELOAD = b'\x00\x08'
CMD_SPRITEUNLOAD = b'\x01\x08'
CMD_SPRITESHOW = b'\x02\x08'
CMD_SPRITEHIDE = b'\x03\x08'
CMD_SPRITECHANGE = b'\x04\x08'
CMD_SPRITECOMMIT = b'\x05\x08'

CMD_END = b'\x00\x00'

CMD_NAMES = {
    CMD_DIALOGUE: 'Dialogue',
    CMD_CHOICE: 'Choice',
    CMD_SLEEP: 'Sleep',
    CMD_JUMP: 'Jump',
    CMD_CONDJUMP: 'Jump',
    CMD_LEVELJUMP: 'Jump',
    CMD_PERFJUMP: 'Jump',
    CMD_CHOICEJUMP: 'Jump',
    CMD_SPRITELOAD: 'Sprite',
    CMD_SPRITEUNLOAD: 'Sprite',
    CMD_SPRITECHANGE: 'Sprite',
    CMD_SPRITESHOW: 'Sprite',
    CMD_SPRITEHIDE: 'Sprite',
    CMD_SPRITECOMMIT: 'Sprite',
    CMD_END: 'End'
}

NAMES = {
    1: "Kanata",
    2: "Rio",
    3: "Kureha",
    4: "Filicia",
    5: "Noel",
    6: "Kyrie",
    7: "Klaus",
    8: "Naomi",
    9: "Carl",
    10: "Maria",
    11: "Yumina",
    12: "Mishio",
    13: "Seiya"
}

ALIGNMENTS = {}
COUNTS = {}

def indent(text, n):
    return '\n'.join(' ' * n + line for line in text.strip().split('\n'))


def parse(f):
    # First thing can be either header or first command.
    header = f.read(8)
    if header.startswith(MAGIC):
        magic, number, offset = struct.unpack('<IHH', header)
    else:
        f.seek(0)
        header = b''
        magic = number = offset = 0

    # Command loop.
    history = [None]
    while parse_command(f, history):
        pass

def parse_command(f, history):
    pos = f.tell()
    cmd = f.read(2)

    # We're done here.
    if not cmd:
        return False

    # Record command.
    history.append(cmd)
    if cmd == PADDING:
        return True
    COUNTS[cmd] = COUNTS.get(cmd, 0) + 1

    # Process command.
    length, = struct.unpack('<H', f.read(2))
    if length >= 4:
        content = f.read(length - 4)
    else:
        content = b''

    # Figure out the alignment.
    alignment = None
    if history[-2] == PADDING:
        alignment = 4
    elif pos % 4 == 2 or length < 8:
        alignment = 2

    if alignment:
        if cmd not in ALIGNMENTS or ALIGNMENTS[cmd] in (0, alignment):
            ALIGNMENTS[cmd] = alignment
        else:
            raise ValueError('Conflicting alignment requirements (got {}, expected {})'.format(alignment, ALIGNMENTS[cmd]))
    else:
        if cmd not in ALIGNMENTS:
            ALIGNMENTS[cmd] = 0

    # Parse possible arguments.
    if length == 4:
        args = ''
    else:
        args = struct.unpack('<{}H'.format(length // 2 - 2),  content)
        args = ' '.join(str(i) for i in args)

    # Visualize command.
    name = CMD_NAMES.get(cmd, 'CMD [{}]'.format(' '.join(hex(x) for x in reversed(cmd))))
    parser = 'parse_{}'.format(name.lower())
    print('- {} ({} bytes, offset {}, alignment {}) {}'.format(name, length, pos, alignment if alignment else 'unknown', args))

    if parser in globals():
        globals()[parser](cmd, content, pos)

    return True

def parse_dialogue(cmd, contents, pos):
    voice, character, index = struct.unpack("<III", contents[:12])
    encoded = contents[12:]
    dialogue = encvis.decode(encoded)
    # if bytes(encvis.encode(dialogue)) != encoded:
    #     raise ValueError('encvis failure: {} // {} // {}'.format(encoded, dialogue, bytes(encvis.encode(dialogue))))

    voicemsg = 'voice #{}'.format(voice) if voice != 0xFFFFFFFF else 'no voice'
    msg = '  @{} [{}] {}:\n{}'.format(index, voicemsg, NAMES.get(character, hex(character)[:2]), indent(dialogue, 4))
    print(msg)

def parse_choice(cmd, contents, pos):
    amount, index = struct.unpack('<HH', contents[:4])
    offsets = struct.unpack('<{}I'.format(amount), contents[4:4 + 4 * amount])
    choices = [ encvis.decode(contents[i - 4:].partition(b'\x00')[0]) for i in offsets ]

    choicemsg = '\n'.join('#{}: {}'.format(i + 1, choice) for i, choice in enumerate(choices))
    msg = '  {} choice{} @{}\n{}'.format(amount, 's' * (amount != 1), index, indent(choicemsg, 4))
    print(msg)

def parse_jump(cmd, contents, pos):
    if cmd == CMD_CHOICEJUMP:
        index, target = struct.unpack('<2H', contents)
        type = 'Choice #{}'.format(index)
    elif cmd == CMD_PERFJUMP:
        value, target, var = struct.unpack('<3H', contents)
        type = 'Performance: {} >= {}'.format(var, value)
    elif cmd == CMD_LEVELJUMP:
        val1, target, val2 = struct.unpack('<3H', contents)
        type = 'Level ({}, {})'.format(val1, val2)
    elif cmd == CMD_CONDJUMP:
        yestarget, notarget, var1, var2, value = struct.unpack('<5H', contents)
        yesoffset = yestarget - pos
        nooffset = notarget - pos
        if pos % 4:
            yesoffset += 2
            nooffset += 2
        msg = '  Conditional: ({}, {}) == {}, Target true: {} [offset +{}], Target false: {} [offset +{}]'.format(var1, var2, value, yestarget, yesoffset, notarget, nooffset)
        print(msg)
        return
    elif cmd == CMD_JUMP:
        target, = struct.unpack('<H', contents)
        type = 'Unconditional'

    offset = target - pos
    if pos % 4:
         offset += 2

    msg = '  {}, Target: {} [offset +{}]'.format(type, target, offset)
    print(msg)

def parse_sprite(cmd, contents, pos):
    if cmd == CMD_SPRITECOMMIT:
        msg = 'Commit changes'
    elif cmd in (CMD_SPRITESHOW, CMD_SPRITEHIDE):
        id, var1, delay = struct.unpack('<3H', contents)
        type = 'Show' if cmd == CMD_SPRITESHOW else 'Hide'
        msg = '{} #{}@{}, delay: {} frames'.format(type, id, var1, delay)
    elif cmd == CMD_SPRITELOAD:
        id, var1, var2 = struct.unpack('<3H', contents)
        msg = 'Load #{}@{}, {}'.format(id, var1, var2)
    elif cmd == CMD_SPRITEUNLOAD:
        id, var1 = struct.unpack('<2H', contents)
        msg = 'Unload #{}@{}'.format(id, var1)
    elif cmd == CMD_SPRITECHANGE:
        id1, var1, id2, var2, delay = struct.unpack('<5H', contents)
        msg = 'Change #{}@{} -> #{}@{}, delay: {} frames'.format(id1, var1, id2, var2, delay)
    print('  {}'.format(msg))

def parse_sleep(cmd, contents, pos):
    delay, = struct.unpack('<H', contents)
    print('  {} frames'.format(delay))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: {} <script> [outfile]'.format(sys.argv[0]))
        sys.exit(1)

    if len(sys.argv) >= 3:
        sys.stdout = open(sys.argv[2], "w", encoding="utf-8")

    with open(sys.argv[1], 'rb') as f:
        parse(f)

# stringcoder.py
# rips strings.

import struct
import re
from io import StringIO, BytesIO
import os
from os import path
import pickle

NAMES = {1: "Kanata", 2: "Rio", 3: "Kureha", 4: "Filicia", 5: "Noel", 6: "Kyrie", 7: "Klaus",
    8: "Naomi", 9: "Carl", 10: "Maria", 11: "Yumina", 12: "Mishio", 13: "Seiya"}
RESNAMES = dict(reversed(i)for i in NAMES.items())

MAGIC = 0x00080410
MAGIC2 = 0xFFFE

CHARRANGES = (
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
    )

SPECIALS = {
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
0x8E0B: 0x9Aa2,
0x8E0C: 0x8C62,
0x8E0D: 0xE359,
0x8E0E: 0xE3A9,
0x8E0F: 0xE4BB,

0x8E10: 0xE748,
0x8E11: 0xE7B3,
0x8E12: 0x96F6,
}

REVSPECIALS = dict(reversed(i)for i in SPECIALS.items())
REVSPECIALS.update({0x8140: 0x8120}) #fix for multiple occurrences like spaces
REVCHARRANGES = tuple(((a+c,b+c),-c) for (a,b),c in CHARRANGES)


HALFMAP = [ord(i) for i in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?\'']

#6x16-2, 94, 5E long rows of Kanji
#strange things start at page 8D and 8E
#Kanji start at 0x8201

#further ranges:
#((0x8201, 0x825E), (0x889F, 0x88FC)) #0x068E

#0x8260 - 0x831F
#((0x8261, 0x829F), (0x8940, 0x897E)) #0x06DF
#((0x82A0, 0x82BE), (0x8980, 0x899E)) #0x06E0
#((0x82C1, 0x831E), (0x899F, 0x89FC)) #0x06DE

#0x8320 - 0x83DF
#((0x8321, 0x835F), (0x8A40, 0x8A7E)) #0x071F
#((0x8360, 0x837E), (0x8A80, 0x8A9E)) #0x0720
#((0x8381, 0x83DE), (0x8A9F, 0x8AFC)) #0x071E

#

def toJIS(character):
    if character in SPECIALS:
        return SPECIALS[character]

    for (lbound, ubound), offset in CHARRANGES:
        if lbound <= character <= ubound:
            return character+offset
    
    if 0x8260 <= character <= 0x8E12:
        d = character - 0x8260
        div = d // 0xC0
        res = d % 0xC0
        base = ((div+0x89)<<8) + res + 0x40
        if 0x01 <= res <= 0x3F:
            return base - 0x1
        elif 0x40 <= res <= 0x5E:
            return base
        elif 0x61 <= res <= 0xBE:
            return base - 0x2
    elif 0x8e20 <= character <= (0x8e20+len(HALFMAP)**2):
        return HALFMAP[(character-0x8e20)//len(HALFMAP)]*0x100+HALFMAP[(character-0x8e20)%len(HALFMAP)]
    else:
        print('assumed unknown character {} was a space'.format(character))
        return 0x8140

def fromJIS(character):
    if character in REVSPECIALS:
        return REVSPECIALS[character]

    for (lbound, ubound), offset in REVCHARRANGES:
        if lbound <= character <= ubound:
            return character+offset

    if 0x8940 <= character <= 0x9FFC:
        d = character - 0x8900
        div = d // 0x100
        res = d % 0x100
        base = 0x8260 + 0xC0*div + res - 0x40
        if 0x40 <= res <= 0x7E:
            return base + 0x1
        elif 0x80 <= res <= 0x9E:
            return base
        elif 0x9F <= res <= 0xFC:
            return base + 0x2
    elif 0x2020 <= character <= 0x7F7F: #handle half width hax shit
        if character//0x100 not in HALFMAP or character%0x100 not in HALFMAP:
            raise ValueError('the half-width-full-width escape {} was not in the range of allowed half-width characters'.format(hex(character)))
        return 0x8e20+len(HALFMAP)*HALFMAP.index(character//0x100)+HALFMAP.index(character%0x100)
    print(character)
    raise ValueError('not a valid pseudo-shift-JIS codepoint')

def isvalid(bytestring):
    firstchar = None
    toprange = (0x8e20+len(HALFMAP)**2)>>8
    for character in bytestring:
        if firstchar:
            firstchar = False
        elif 0x81 <= character <= toprange:
            firstchar = True
        else:
            if not (0x00 <= character <=0x7F):
                break
    else:
        return True
    return False

def isfilevalid(file):
    with open(file, 'rb') as f:
        data = f.read()
    return ((len(data)%16)==0) and isvalid(data)

def dumpstringfile(file, dest):
    with open(file, 'rb') as f:
        data = f.read()
    result = '----------------\n{}\n----------------\n\n----------------'.format(
        decode(data.rstrip(b'\x00')))
    with open(dest, 'wb') as g:
        g.write(result.encode('utf-8'))

def loadstringfile(file, dest):
    with open(file, 'rb') as f:
        data = f.read().decode('utf-8')
    match = re.search('-{10,}\n(.*?)\n-{10,}\n(.*?)\n-{10,}', data, re.DOTALL)
    if match.group(2) and match.group(2).strip():
        string = match.group(2)
    else:
        string = match.group(1)
        print("translation missing")
    result = encode(string).rstrip(b'\x00')
    if (len(result)%16):
        result += (16 - (len(result)%16)) * b'\x00'
    else:
        result += 16 * b'\x00'
    with open(dest, 'wb') as f:
        f.write(result)

def decode(bytestring):
    firstchar = None
    charlist = []
    for character in bytestring:
        if firstchar:
            chars = toJIS((firstchar<<8)+character)
            if chars < 0x8000:
                charlist.append(0x5c)
            charlist.extend([chars>>8, chars&0xFF])
            firstchar = None
        elif 0x81 <= character <= 0x91:
            firstchar = character
        else:
            charlist.append(character)
    # print(bytes(charlist))
    try:
        return bytes(charlist).decode('shift_jis')
    except: #neither of these has the characters exactly how we want them. shift_jis misses circled numbers, x0213 has ~ in the twobyte section
        return bytes(charlist).decode('shift_jisx0213')

def encode(string):
    charlist = []
    firstchar = None
    escapeseq = False
    try:
        estring = string.encode('shift_jis')
    except:
        estring = string.encode('shift_jisx0213')
    try:
        for character in estring:
            if firstchar:
                chars = fromJIS((firstchar<<8)+character)
                charlist.extend([chars>>8, chars&0xFF])
                firstchar = None

            elif character == 0x5c:
                escapeseq = True
            elif 0x81 <= character <= 0x9F or 0xE0 <= character <= 0xFC or escapeseq == True:
                firstchar = character
                escapeseq = False
            else:
                charlist.append(character)
        return bytes(charlist)
    except:
        print("failed at encoding the string: ")
        print(string)
        print("at character:")
        print(character)
        raise
        

def dump(file, dest):
    #dump strings from file
    with open(file, 'rb') as f:
        a = Script(f)

    b = ["Script {}, no {}, line offset {}".format(file, a.number, a.line_offset)]
    for i in a.strings:
        b.append(Parser.assemble_scriptline(i))

    c = '\n\n'.join(b).encode('utf-8')+b'\n'
    with open(dest, 'wb') as f:
        f.write(c)
    return a.meta()

def load(meta, file, dest):
    with open(file, 'rb') as f:
        stringobjs= Parser(f).parse_script()
    a = Script.unmeta(meta, stringobjs)
    with open(dest, 'wb') as f:
        f.write(a.content())

def walk(dir):
    dirs = [path.join(dir, i) for i in os.listdir(dir) if path.isdir(path.join(dir, i))]
    files = [path.join(dir, i) for i in os.listdir(dir) if path.isfile(path.join(dir, i)) and not i.endswith('.txt')]
    for file in files:
        print('decompiling '+file)
        with open(file, 'rb') as f:
            magic = f.read(4)
        if magic != b'\x10\x04\x08\x00':
            continue
        try:
            dump(file, file+'.txt')
        except:
            print('file: '+file)
            raise
    for dir in dirs:
        walk(dir)

#how to scan for strings:
#first scan all commands.
#first 12 bytes are the header

class Script:
    def __init__(self, fileobj=None):
        self.parse(fileobj)

    def parse(self, f):
        self.strings = []
        self.commands = []
        self.jumps = []
        positions = {} # location: index

        data = f.read(11)
        if len(data) == 10:
            self.header = f.read()
            return 
            # raise ValueError('empty script object (or whatever these files are)')
        f.seek(0)
        self.header = f.read(8) #technically this is the first command, but we'll make an exception
        if self.header.startswith(b'\x10\x04\x08\x00'):
            self.magic, self.number, self.line_offset = struct.unpack("<IHH", self.header)
        else:
            self.magic = 0x0
            self.number = 0x0
            self.line_offset = 0x0
            f.seek(0)
            self.header = b''
        while True:
            pos = f.tell()
            commandid = f.read(2)

            if commandid == b'\xff\xff':
                continue #padding
            elif not commandid: #eof
                break

            positions[pos] = len(self.commands)

            length, = struct.unpack("<H", f.read(2))
            if commandid == b'\x00\x00' and length==0: #padded with 0's at the end
                break
            content = f.read(length - 4)

            if commandid == b'\xFE\xFF':
                command = ScriptString(commandid, content)
                self.strings.append(command)
            elif commandid == b'\xFC\xFF':
                command = ChoiceString(commandid, content)
                self.strings.append(command)
            elif commandid == b'\x07\x04':
                command = Jump(commandid, content)
                self.jumps.append(command)
            elif commandid == b'\x1F\x04':
                command = ConditionalJump(commandid, content)
                self.jumps.append(command)
            elif commandid == b'\x36\x04':
                command = RehearsalJump(commandid, content)
                self.jumps.append(command)
            elif commandid == b'\x03\x00':
                command = OtherJump(commandid, content)
                self.jumps.append(command)
            elif commandid == b'\x04\x00':
                command = ShortJump(commandid, content)
                self.jumps.append(command)
            else:
                command = Command(commandid, content)
            self.commands.append(command)

        for jump in self.jumps:
            if jump.target in positions:
                jump.target = positions[jump.target]
            elif jump.target + 2 in positions:
                jump.target = positions[jump.target + 2]
            else:
                raise ValueError("Jump without clear target")

    def content(self):
        positions = [] # command_index - startpos
        jumpoffsets = []

        #assemble everything
        result = list(self.header)
        for i, command in enumerate(self.commands):
            #check if it needs padding
            if (len(result) % 4 == 2):
                directive, type = command.magic
                if type == 0x00:
                    if directive == 0x0D:
                        result.extend(list(b'\xFF\xFF'))
                elif type == 0x08:
                    if directive not in (0x05, 0x08, 0x09, 0x0F, 0x1A):
                        result.extend(list(b'\xFF\xFF'))
                elif type == 0x0C:
                    if directive in (0x00, 0x04, 0x08, 0x0C, 0x0e):
                        result.extend(list(b'\xFF\xFF'))
                elif type == 0xFF:
                    result.extend(list(b'\xFF\xFF'))

            positions.append(len(result))
            if isinstance(command, Jump):
                jumpoffsets.append(len(result))
            result.extend(list(command.content()))

        # figure out the new jump locs. requires some backtracking
        for jump, jumpoffset in zip(self.jumps, jumpoffsets):
            loc = jumpoffset + jump.offset
            result[loc : loc + 2] = struct.pack("<H", positions[jump.target])

        return bytes(result)

    def meta(self):
        #purge strings from self and return self
        for string in self.strings:
            string.clean()
        return {'evscript':self}

    @classmethod
    def unmeta(self, meta, stringobjs):
        obj = meta['evscript']
        if len(stringobjs) != len(obj.strings):
            raise Exception('number of strings for repacking does not match')
        for i in range(len(obj.strings)):
            obj.strings[i].set(stringobjs[i])
        return obj

    def __bytes__(self):
        return self.content()

class Command:
    def __init__(self, type, contents):
        self.magic = type
        self.contents = contents

    def content(self, address=None):
        return struct.pack("<2sH"+str(len(self.contents))+"s", self.magic, len(self.magic)+len(self.contents)+2, self.contents)

    def __bytes__(self):
        return self.content()


CANARY = 0xCCCC

class Jump(Command):
    offset = 6
    # 04 07
    def __init__(self, type, contents):
        self.magic = type
        self.id, self.target = struct.unpack("<HH", contents)

    def content(self):
        return struct.pack("<2sHHH", self.magic, 8, self.id, CANARY)


class OtherJump(Jump):
    offset = 4
    # 00 03
    def __init__(self, type, contents):
        self.magic = type
        self.target, self.a, self.b, self.c, self.d = struct.unpack("<HHHHH", contents)

    def content(self):
        return struct.pack("<2sHHHHHH", self.magic, 14, CANARY, self.a, self.b, self.c, self.d)


class ShortJump(Jump):
    offset = 4
    # 00 04
    def __init__(self, type, contents):
        self.magic = type
        self.target, = struct.unpack("<H", contents)

    def content(self):
        return struct.pack("<2sHH", self.magic, 6, CANARY)


class ConditionalJump(Jump):
    # 04 1F
    def __init__(self, type, contents):
        self.magic = type
        self.type, self.target, self.value = struct.unpack("<HHH", contents)

    def content(self):
        return struct.pack("<2sHHHH", self.magic, 10, self.type, CANARY, self.value)


class RehearsalJump(Jump):
    # 04 36 type target value
    def __init__(self, type, contents):
        self.magic = type
        self.type, self.target, self.value = struct.unpack("<HHH", contents)

    def content(self):
        return struct.pack("<2sHHHH", self.magic, 10, self.type, CANARY, self.value)



class ScriptString(Command):
    def __init__(self, type=None, contents=None, **kwargs):
        if type:
            self.magic = type
            self.voice, self.character, self.index = struct.unpack("<III", contents[:12])
            bytestring = contents[12:]
            try:
                self.string = decode(bytestring.rstrip(b'\x00'))
            except:
                print('an error occured while decoding: ')
                print(bytestring.rstrip(b'\x00'))
                raise
        else:
            self.clean()
            for key in kwargs:
                setattr(self, key, kwargs[key])

    def clean(self):
        self.magic = b'\xfe\xff'
        self.string = ""
        self.character = 0
        self.index = 0xFFFFFFFF
        self.voice = 0xFFFFFFFF

    def set(self, stringobj):
        self.magic = stringobj.magic
        self.string = stringobj.string
        self.character = stringobj.character
        self.index = stringobj.index
        self.voice = stringobj.voice

    def content(self, address=None):
        bytestring = encode(self.string)
        if len(bytestring)%2 == 0:
            bytestring += b'\x00\x00'
        else:
            bytestring += b'\x00'
        length = len(bytestring)+16
        return struct.pack("<2sHIII"+str(len(bytestring))+"s", self.magic, length, self.voice, self.character, self.index, bytestring)


class ChoiceString(Command):
    def __init__(self, type=None, contents=None, **kwargs):
        if type:
            self.magic = type
            choicesamount, self.index = struct.unpack("<HH", contents[:4])
            choiceoffsets = struct.unpack("<"+str(choicesamount)+"I", contents[4:4+4*choicesamount])
            choicestrings = (contents[i-4:].split(b'\x00',1)[0] for i in choiceoffsets)
            self.choices = []
            for i in choicestrings:
                try:
                    self.choices.append(decode(i))
                except:
                    print('an error occured while decoding: ')
                    print(bytestring.rstrip(b'\x00'))
                    raise
        else:
            self.clean()
            for key in kwargs:
                setattr(self, key, kwargs[key])
                
    def clean(self):
        self.magic = b'\xfc\xff'
        self.index = 0
        self.choices = []
        
    def set(self, stringobj):
        self.magic = stringobj.magic
        self.choices = stringobj.choices
        self.index = stringobj.index
        
    def content(self, address=None):
        offsets = []
        curroffset = 0
        bytestrings = []
        amount = len(self.choices)
        for i in self.choices:
            bytestring = encode(i) + b'\x00'
            offsets.append(curroffset)
            curroffset += len(bytestring)
            bytestrings.append(bytestring)
        
        finalstring = b''.join(bytestrings)
        if len(finalstring)%2 == 1:
            finalstring += b'\x00'
            
        offsets = [i+8+4*amount for i in offsets]
        length = 4+4+4*amount+len(finalstring) #header/len, amount/index, offsets, string
        return struct.pack("<2sHHH"+str(amount)+"I"+str(len(finalstring))+"s", self.magic, length, amount, self.index, *(offsets+[finalstring]))
        

class Parser:
    """This code is horrible, when the fuck did I write this"""
    def __init__(self, scriptbuffer):
        self.buffer = BytesIO(scriptbuffer.read().replace(b'\r',b'')) #fuck carriage returns
        self.warned = False

    @classmethod
    def assemble_scriptline(self, scriptstring):
        if isinstance(scriptstring, ScriptString):
            return '{} {} {}\n--------\n{}\n--------\n{}\n--------\n'.format(
                hex(scriptstring.index)[2:],
                hex(scriptstring.voice)[2:] if scriptstring.voice!=0xFFFFFFFF else 'None',
                NAMES.get(scriptstring.character, hex(scriptstring.character)[2:]),
                scriptstring.string,
                "")
        elif isinstance(scriptstring, ChoiceString):
            return '\n--------\n'.join(['CHOICES '+str(len(scriptstring.choices))+' '+str(scriptstring.index)]+scriptstring.choices+['']*(len(scriptstring.choices)+1))

    def warn_missing_translation(self):
        if not self.warned:
            print("translation missing")
            self.warned = True

    def parse_script(self):
        lines = []
        header = self.parse_upto([b'\n'])
        self.skip_whitespace()
        try:
            while self.read_ahead() != b'':
                lines.append(self.parse_scriptline())
                self.skip_whitespace()
        except:
            print(b'\n****\n'.join(i.string.encode('utf-8') for i in lines))
            raise
        return lines

    def parse_scriptline(self):
        start = self.parse_word()
        if start == b'CHOICES':
            amount = self.parse_number(self.parse_word(), hex=False)
            index = self.parse_number(self.parse_word(), hex=False)
            choices = [i.decode('utf-8') for i in self.parse_choices(amount)]
            return ChoiceString(choices=choices, index=index)
        else:
            index = self.parse_number(start, hex=True)
            voice = self.parse_word()
            voice = 0xFFFFFFFF if voice == b'None' else self.parse_number(voice, hex=True)
            name = self.parse_word().decode('utf-8')
            character = RESNAMES[name] if name in RESNAMES else self.parse_number(name, hex=True)
            string = self.parse_scriptstring(index).decode('utf-8')
            return ScriptString(index=index, character=character, string=string, voice=voice)
            

    def parse_word(self):
        self.skip_whitespace()
        word = self.parse_upto()
        return word

    def parse_number(self, word, hex=False):
        return int(word, 16 if hex else 10)

    def parse_upto(self, upto=[b'\n',b'\t',b'\v',b'\r',b' '], swallow=False):
        next = []
        while not any((b''.join(next[-len(i):]) == i) for i in upto):
            next.append(self.buffer.read(1))
            if next[-1] == b'':
                break
        for i in upto:
            if b''.join(next).endswith(i):
                break
        if not swallow:
            self.buffer.seek(-len(i), os.SEEK_CUR)
            return b''.join(next[:-len(i)])
        else:
            return b''.join(next[:-len(i)])

    def skip_whitespace(self):
        next = b' '
        while next in b'\n\t\v\r ' and next != b'':
            next = self.buffer.read(1)
        if next != b'':
            self.buffer.seek(-1, os.SEEK_CUR)

    def read_ahead(self):
        ahead = self.buffer.read(1)
        if ahead != b'':
            self.buffer.seek(-1, os.SEEK_CUR)
        return ahead

    def validate_translation(self, lineno, string):
        # validate a translation according to some rules
        lines = string.decode("utf-8").split("\n")
        # remove the trainling newline
        lines.pop()

        if len(lines) > 3:
            print("Translation has too many lines at line {}".format(lineno))

        if any(len(i) > 46 for i in lines):
            print("Translation line too long at line {}".format(lineno))

        if lines[0].startswith("("):
            if any(i and not i.startswith(" ") and (len(i) == 1 or i[1] != " "[0]) for i in lines[1:]):
                print("Translation parenthesis indentation error at line {}".format(lineno))       

        
    def parse_scriptstring(self, lineno):
        self.skip_whitespace()
        header = self.buffer.read(9)
        if header != b'--------\n':
            raise ValueError('expected ScriptString, got {} {}'.format(string, self.buffer.read(100)))
        string = self.parse_upto([b'\n--------\n'], True)
        replstring = self.parse_upto([b'\n--------\n'], True)
        if replstring and replstring.strip():
            if not replstring.endswith(b'\n'):
                replstring += b'\n'
            string = re.sub(b'\\[',b'[',b''.join(re.split(b'(?<!\\\\)\\[[^\\[\\]]*\\]', replstring)))
            self.validate_translation(lineno, string)
        else:
            self.warn_missing_translation()

        return string
        
    def parse_choices(self, amount):
        self.skip_whitespace()
        header = self.buffer.read(9)
        if header != b'--------\n':
            raise ValueError('expected ScriptString, got {} {}'.format(string, self.buffer.read(100)))
        japanese = []
        translated = []
        for i in range(amount):
            japanese.append(self.parse_upto([b'\n--------\n'], True))
        for i in range(amount):
            temp = self.parse_upto([b'\n--------\n'], True)
            if temp and temp.strip():
                temp = re.sub(b'\\[',b'[',b''.join(re.split(b'(?<!\\\\)\\[[^\\[\\]]*\\]', temp))).replace(b'\n', b'')
                if len(re.sub(rb"\\.", b"", temp)) > 23:
                    print("Choice translation line too long")
            else:
                self.warn_missing_translation()
                temp = japanese[i]

            translated.append(temp)
        return translated
            
            


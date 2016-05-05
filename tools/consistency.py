# consistency.py
# checks if all the same japanese text has the same translation
# borrows code from ev.py to make sure the parsing is the same

import util
import ev
import re
import os

def main(folder):
    transdict = {} # will be formatted as {jap: {translation: [(file, line, translation)*]}}
    util.walk(folder, testfile, transdict)    
    
    fixlist = []
    for i in transdict:
        if len(transdict[i]) > 1:
            # different translations
            keyname = min(min(k[0]+'_'+k[1] for k in transdict[i][j]) for j in transdict[i])
            try:
                fixlist.append((
                    ('differences between:\n' +
                        '\nand\n'.join(
                            ', '.join(
                                "file {} line {}".format(*k) for k in transdict[i][j]
                            ) + '\n[[[{}]]]'.format(j.decode('utf-8'))
                            for j in transdict[i]
                        ) + '\n\n'
                    ), keyname
                ))
            except UnicodeDecodeError:
                print("failed on", keyname, i)
                for j in transdict[i]:
                    try:
                        j.decode('utf-8')
                    except:
                        print(j, transdict[i][j])
                raise
    
    with open('consistency.txt', 'w', encoding='utf-8') as g:
        g.write(''.join(i[0] for i in sorted(fixlist, key = lambda x: x[1])))
    return transdict

   
def testfile(fname, transdict):
    shortname = fname.rsplit("data.afs" + os.sep, 1)[1]
    filename = fname.rsplit(os.sep, 1)[1]
    if not filename.endswith(".txt"):
        return
    if filename.startswith('.') or filename.endswith('~') or 'ev99' in fname or "conflicted" in filename:
        return
    with open(fname, 'rb') as f:
        start = f.read(10)
        f.seek(0)
        if b'-------' in start:
            linelist = parsestringfile(f, shortname)
        else:
            linelist = Parser(f).parse_script(shortname)
            
    for i in linelist:
        if i[3] not in transdict:
            a = transdict[i[3]] = {}
        else:
            a = transdict[i[3]]
        if i[2] not in a:
            b = a[i[2]] = []
        else:
            b = a[i[2]]
        b.append(tuple(i[0:2]))

def parsestringfile(f, fname):
    data = f.read()
    match = re.search(b'-{10,}\n(.*?)\n-{10,}\n(.*?)\n-{10,}', data, re.DOTALL)
    return [(fname, '0', match.group(2), match.group(1))]
        
class Parser(ev.Parser):
    def parse_script(self, fname):
        linelist = []
        header = self.parse_upto([b'\n'])
        self.skip_whitespace()
        while self.read_ahead() != b'':
            self.parse_scriptline(fname, linelist)
            self.skip_whitespace()
        return linelist
        
    def parse_scriptline(self, fname, linelist):
        start = self.parse_word()
        if start == b'CHOICES':
            amount = self.parse_number(self.parse_word(), hex=False)
            index = self.parse_number(self.parse_word(), hex=False)
            japanese, translated = self.parse_choices(amount)
            for i, jap in enumerate(japanese):
                linelist.append((fname, 'CHOICE{}'.format(i), translated[i], jap))
        else:
            index = self.parse_number(start, hex=True)
            voice = self.parse_word()
            voice = 0xFFFFFFFF if voice == b'None' else self.parse_number(voice, hex=True)
            name = self.parse_word().decode('utf-8')
            character = ev.RESNAMES[name] if name in ev.RESNAMES else self.parse_number(name, hex=True)
            japanese, translated = self.parse_scriptstring()
            linelist.append((fname, hex(index)[2:], translated, japanese))
        
    def parse_scriptstring(self):
        self.skip_whitespace()
        header = self.buffer.read(9)
        if header != b'--------\n':
            raise ValueError('expected ScriptString, got {} {}'.format(string, self.buffer.read(100)))
        string = self.parse_upto([b'\n--------\n'], True)
        replstring = self.parse_upto([b'\n--------\n'], True)
        
        if not replstring.endswith(b'\n'):
            replstring += b'\n'

        string = re.sub(b'\\[',b'[',b''.join(re.split(b'(?<!\\\\)\\[[^\\[\\]]*\\]', string)))
        replstring = re.sub(b'\\[',b'[',b''.join(re.split(b'(?<!\\\\)\\[[^\\[\\]]*\\]', replstring)))
        return string, replstring
        
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
            temp = temp if temp else japanese[i]
            temp = re.sub(b'\\[',b'[',b''.join(re.split(b'(?<!\\\\)\\[[^\\[\\]]*\\]', temp))).replace(b'\n', b'')
            translated.append(temp)
        return japanese, translated


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        exit('usage: {} folder'.format(sys.argv[0]))
    a = main(sys.argv[1])
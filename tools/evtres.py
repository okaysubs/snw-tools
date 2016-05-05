# findstrings
# look for any strings in the format "00 ........ 0A 00" in evt files
import os
from os import path
import re
import sys

FINDRE = re.compile(b'\xFE\xFF.{12}\x00*?([^\x00]+\x0A)\x00', re.DOTALL)
CHARRE = re.compile(b'\xFE\xFF.{4}(.)', re.DOTALL)
firstbyte = []
secondbytedict = {}
secondbyte = []

def main(folder, outfile):
    with open(outfile,'wb') as g:
        lookthrough(folder, g)

def lookthrough(folder, g):
    for item in os.listdir(folder):
        if path.isdir(path.join(folder, item)):
            lookthrough(path.join(folder, item), g)
        else:
            findstrings(path.join(folder, item), g)

def findstrings(file, g):
    with open(file, 'rb') as f:
        data = f.read()
    matches = FINDRE.findall(data)
    characters = CHARRE.findall(data)
    g.write(b'####new file "' + file.encode('utf-8') + b'" ####\n')
    g.write(b'the characters are:')
    g.write(b'-'.join([str(i[0]).encode('ascii') for i in characters]))
    g.write(b'\n')
    g.write(b'----------------------\n')
    g.write(b'----------------------\n'.join([expandcode(i) for i in matches]))

def expandcode(bytestring):
    #takes a one length bytes object and returns an int representing the proper codepage place in shift-jis
    resultarray = []
    sjisseq = False
    global firstbyte
    global secondbytedict
    global secondbyte
    for char in bytestring:
        if sjisseq == False:
            firstbyte.append(char)
            #if char < 0x80:
            #    resultarray.append(char)
            #elif char < 0x99:
            #    sjisseq = True
            #    resultarray.append(char+1)
            #elif char < 0xE8:
            #    sjisseq = True
            #   resultarray.append(char+2)
            #else:
            #    sjisseq = True
            if char > 0x7F:
                sjisseq = True
            resultarray.append(char)
        else:
            sjisseq = False
            secondbyte.append(char)
            if not firstbyte[-1] in secondbytedict:
                secondbytedict[firstbyte[-1]] =[char]
            else:
                secondbytedict[firstbyte[-1]].append(char)

            firstbyte[-1], char = getproperbytes(firstbyte[-1], char)
            resultarray.append(char)
    return bytes(resultarray)


    #if every 0x40 at the start was removed
    #then to get the proper place:

def getproperbytes(firstbyte, secondbyte):
    #YYYYYYYY YYYYYYYY YYYYYYYY YYYYYYYYY
    #XXYYYYYY XXYYYYYY XXYYYYYY XXYYYYYYY XXYYYYYY XXYYYYYY
    secondbyte = secondbyte+0x3f*(firstbyte-0x80)
    firstbyte += secondbyte//0xFF
    secondbyte = secondbyte%0xFF
    return firstbyte, secondbyte


def charanalysis(file):
    global secondbytedict
    testdict = {key: list(sorted(list(set(secondbytedict[key])))) for key in secondbytedict}
    with open(file, 'w') as f:
        for key in testdict:
            codepage = testdict[key]
            f.write('new codepage {}\n'.format(key))
            for i in range(16):
                f.write('    ')
                for j in range(16):
                    if 16*i+j in codepage:
                        f.write('X')
                    else:
                        f.write(' ')
                f.write('\n')

if __name__ == "__main__":
    if len(sys.argv)<3:
        exit("usage: {} folder outfile".format(sys.argv[0]))

    main(sys.argv[1], sys.argv[2])
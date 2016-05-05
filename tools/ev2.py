# another script tryout
import struct

def dissassemble(file):
    global before, after
    with open(file, 'rb') as f:
        commands = []
        printnextone = False
        while True:
            commandid = f.read(2)
            if not commandid:
                break
            elif commandid == b'\xff\xff':
                if len(commands[-1]) == 8:
                    before.append( tohex(commands[-1]))
                printnextone = True
                commands.append(commandid)
            else:
                lengthstr = f.read(2)
                length, = struct.unpack('<H', lengthstr)
                data = f.read(length-4)
                commands.append(commandid+lengthstr+data)
                if printnextone:
                    printnextone = False
                    if len(commands[-1]) == 8:
                        after.append(tohex(commands[-1]))

    with open(file+'.dis.txt', 'wb') as f:
        f.write(b'\n\n'.join([tohex(command) for command in commands]))

def tohex(bytestring):
    return ' '.join([('0' if len(hex(i)) == 3 else '') +hex(i)[2:].upper() for i in bytestring]).encode('ascii')

before = []
after = []

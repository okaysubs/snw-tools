import os
from os import path
import sys
import shutil

def replacedata(old, new):
    for file in os.listdir(old):
        relpath = file.replace("_","/")
        oldpath = path.join(old, file)
        newpath = path.join(new, relpath)
        if path.isfile(oldpath):
            shutil.copy2(oldpath, newpath)
        print ("%s -> %s" % (oldpath, newpath))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        exit('usage: {} <old> <new>'.format(sys.argv[0]))
    else:
        replacedata(sys.argv[1], sys.argv[2])










# alter.py
# recursively walks a folder and alters files where necessary based on another folder.
import os
from os import path
import shutil
import sys

def alter(base, replacement):
    alter_folder(base, replacement)


def alter_folder(folder, replacementfolder):
    subfolders = [i for i in os.listdir(folder) if path.isdir(path.join(folder, i))]
    files = [i for i in os.listdir(folder) if path.isfile(path.join(folder, i))]

    replacementsubfolders = [i for i in os.listdir(replacementfolder) if path.isdir(path.join(replacementfolder, i))]
    replacementfiles = [i for i in os.listdir(replacementfolder) if path.isfile(path.join(replacementfolder, i))]

    interestingfolders = [i for i in subfolders if i in replacementsubfolders]
    interestingfiles = [i for i in files if i in replacementfiles]


    for file in interestingfiles:
        shutil.copy2(path.join(replacementfolder, file), path.join(folder, file))
        

    for i in interestingfolders:
        alter_folder(path.join(folder, i), path.join(replacementfolder, i)) 

if __name__ == "__main__":
    if len(sys.argv) < 3:
        exit("usage: {} base replacement".format(sys.argv[0]))

    alter(sys.argv[1], sys.argv[2])
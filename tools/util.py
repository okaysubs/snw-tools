#util.py
#utility stuff
import os
from os import path

def walk(folder, function, *args, **kwargs):
    subs = (path.join(folder, i) for i in os.listdir(folder))
    for item in subs:
        if path.isfile(item):
            try:
                function(item, *args, **kwargs)
            except Exception as e:
                print('an exception happened while walking file {}: {}'.format(item, e))
        else:
            walk(item, function, *args, **kwargs)

def findinfile(file, bytestring):
    #print('walking {}'.format(file))
    with open(file, 'rb') as f:
        data = f.read()
    if bytestring in data:
        print('found the string in file {}'.format(file))

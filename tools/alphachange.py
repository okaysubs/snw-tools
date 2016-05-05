from PIL import Image
import sys

if len(sys.argv) < 4:
    exit("usage: {} file dest alpha".format(sys.argv[0]))

image = Image.open(sys.argv[1])
if image.mode != 'RGBA':
    image = image.convert('RGBA')
data = image.load()

alpha = int(sys.argv[3][2:], 16) if sys.argv[3].startswith('0x') else int(sys.argv[3])

for x in range(image.size[0]):
    for y in range(image.size[1]):
        temp = data[x,y]
        data[x,y] = temp[0], temp[1], temp[2], alpha

image.save(sys.argv[2])
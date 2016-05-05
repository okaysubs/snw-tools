# gim.py
# converts gim's to png's and back again
# need to have gimconv available. it's expected to be at gimconv/gimconv.exe
import sys

MAGIC = b'GIM.'

def gim_to_image(input, out):
    if sys.platform == 'win32':
        os.system('gimconv\gimconv {} -o {}}'.format(input.replace('/','\\'), out.replace('/','\\')))

def image_to_gim(input, out):
    if sys.platform == 'win32':
    	# not sure if these files will still work
        os.system('gimconv\gimconv {} -pictures -o {}}'.format(input.replace('/','\\'), out.replace('/','\\')))

if __name__ == '__main__':

	if len(sys.argv)<4:
		exit('usage: {} in out mode'.format(sys.argv[0]))

	if sys.argv[3].lower() == 'read':
		gim_to_image(sys.argv[1], sys.argv[2])
	else:
		image_to_gim(sys.argv[1], sys.argv[2])


import sys
import io
import evis
from util import walk

search = None

def _scan_file(filename):
    sys.stdout = io.StringIO()
    if filename.endswith(".txt") and not "AR" in filename:
        sys.__stdout__.write('scanning ' + filename + ' \n')
        with open(filename[:-4], "rb") as f:
            evis.parse(f)
        if search:
            needle = '[0x{} 0x{}]'.format(search[:2].lower().lstrip('0') or '0', search[2:].lower().lstrip('0') or '0')
            haystack = sys.stdout.getvalue()
            if needle in haystack:
                sys.__stdout__.write('MATCH in {} ({} occurences)\n'.format(filename, haystack.count(needle)))

def build_table(folder, tablefile):
    walk(folder, _scan_file)
    with open(tablefile, "w", encoding="utf-8") as outfile:
        for key, value in evis.ALIGNMENTS.items():
            print(hex(key[1])[2:].zfill(2), hex(key[0])[2:].zfill(2), value, evis.COUNTS[key], file=outfile)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('usage: {} <script> <outfile> <tablefile> [search]'.format(sys.argv[0]))
        sys.exit(1)
    if len(sys.argv) == 5:
        search = sys.argv[4]

    sys.stdout = open(sys.argv[2], "w", encoding="utf-8")
    build_table(sys.argv[1], sys.argv[3])

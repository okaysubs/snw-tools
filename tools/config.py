# config.py
# stores some config for unpacking/repacking to speed things up
import hashlib

skipfolders = [ #doesn't do so much because most of these are inside the AFS archive
'AX0',
'AX1',
'BG',
'BM001',
'BM002',
'BM003',
'BM004',
'BM005',
'BM006',
'BM007',
'BM008',
'BM009',
'BM010',
'BM011',
'ch0',
'ch001',
'ch1',
'ch002',
'ch003',
'ch004',
'ch005',
'ch006',
'ch007',
'ch008',
'ch009',
'ch010',
'ch011',
'ch012',
'ch013',
'ch014',
'SC',
'se000_',
'se001_',
'se002_',
'se003_',
'se004_',
'se005_',
'se006_',
'se007_',
'se008_',
'se009_',
'se010_',
'se011_',
'se012_',
'se049_',
'se050_',
'se999_',
'SN'
]

def hashfile(file):
	with open(file, 'rb') as f:
		return hashlib.md5(f.read()).digest()
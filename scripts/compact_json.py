#!/usr/bin/python2
import sys, json

for fname in sys.argv[1:]:
	data = json.loads(open(fname).read())
	jstr = json.dumps(data, sort_keys=True, separators=(',', ':'))
	open(fname, 'w').write(jstr)


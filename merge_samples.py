#! /usr/bin/env python
# merge samples: hadd rootfiles inside directories

import os
import sys
import glob

if len(sys.argv) < 2:
    print 'usage: merge_samples.py [-f] directories'
    sys.exit(1)

do = False
if sys.argv[1] == '-f':
    do = True
    tomerge = [ i for i in sys.argv[2:] ]
else:
    tomerge = [ i for i in sys.argv[1:] ]


for i in tomerge:

    target = i.replace('user.falonso.', '')

    cmd = 'hadd %s %s/*root*' % (target, i)

    print cmd
    if do:
        os.system(cmd)



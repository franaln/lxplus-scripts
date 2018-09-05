#! /usr/bin/env python
# merge samples: hadd rootfiles inside directories

import os
import sys
import argparse
import glob

parser = argparse.ArgumentParser(description='')

parser.add_argument('files', nargs='+')
parser.add_argument('-d', dest='do', action='store_true', help='do!')
parser.add_argument('-f', dest='force', action='store_true', help='use hadd -f')

args = parser.parse_args()

tomerge = args.files


for i in tomerge:

    target = i.replace('user.falonso.', '')

    if args.force:
        cmd = 'hadd -f %s %s/*root*' % (target, i)
    else:
        cmd = 'hadd %s %s/*root*' % (target, i)

    print cmd
    if args.do:
        os.system(cmd)



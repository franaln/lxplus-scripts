#! /usr/bin/env python

# rucio_merge.py
# merge downloaded samples

import os
import sys
import argparse


def get_downloaded_samples(input_file, ext=''):

    samples = []
    for line in open(input_file).read().split('\n'):

        if not line or line.startswith('#'):
            continue

        if line.endswith('/'):
            line = line[:-1]

        sample = '%s%s' % (line, ext)
        
        samples.append(sample)

    return samples


# main
parser = argparse.ArgumentParser(description='rucio_merge.py')

parser.add_argument('filepath', nargs='+')
parser.add_argument('-f', dest='force', action='store_true', help='Use hadd -f')
parser.add_argument('-d', dest='dry', action='store_true', help='Dry run: only show commands')
parser.add_argument('-k', dest='keep_user', action='store_true', help='Keep "user.USERNAME" in output name')
parser.add_argument('-r', dest='remove_extension', action='store_true', help='Remove extension "_SOMETHING" at the end of container name')

if len(sys.argv) < 2:
    parser.print_usage()
    sys.exit(1)

args = parser.parse_args()

# txt input file with a list of samples
if len(args.filepath) == 1 and args.filepath[0].endswith('.txt'):
    samples = get_downloaded_samples(args.filepath)

# one or more download samples (can be used with bash * expansions)
else:
    samples = args.filepath


for sam in samples:

    output_name = sam

    if output_name.startswith('user.') and not args.keep_user:
        user = output_name.split('.')[1]
        output_name = output_name[len('user.%s.' % user):]
    if args.remove_extension:
        ext = output_name.split('_')[-1]
        output_name = output_name[:-len('_%s' % ext)]

    output_name += '.root'

    hadd_cmd = 'hadd -f' if args.force else 'hadd'

    cmd = '%s %s %s/*root*' % (hadd_cmd, output_name, sam)

    print(cmd)
    if not args.dry:
        os.system(cmd)



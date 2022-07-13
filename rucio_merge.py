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



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='rucio_merge.py')

    parser.add_argument('filepath', nargs='?')
    parser.add_argument('-f', dest='force', action='store_true', help='Use hadd -f')
    parser.add_argument('-d', dest='dry', action='store_true', help='Dry run: only show commands')

    if len(sys.argv) < 2:
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()

    samples = get_downloaded_samples(args.filepath)

    for sam in samples:

        output_name = sam

        if sam.startswith('user.'):
            user = sam.split('.')[1]
            output_name = output_name.replace('user.%s.' % user, '')

        hadd_cmd = 'hadd -f' if args.force else 'hadd'

        cmd = '%s %s %s/*root*' % (hadd_cmd, output_name, sam)

        print cmd
        if not args.dry:
            os.system(cmd)



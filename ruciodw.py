#! /usr/bin/env python

# ruciodw.py
# download, using rucio, all the samples from the input txt file

import os
import sys
import argparse

def get_download_samples(input_file, ext=''):

    samples = []

    for line in open(input_file).read().split('\n'):

        if not line or line.startswith('#'):
            continue

        if line.endswith('/'):
            line = line[:-1]

        sample = '%s%s' % (line, ext)
        
        samples.append(sample)

    return samples


def download(input_file, log_file, ext=''):

    os.system('rm -f %s' % log_file)

    for sample in get_download_samples(input_file, ext):

        print('> Downloading: %s' % sample)

        cmd = 'rucio download %s | tee -a %s' % (sample, log_file)
        os.system(cmd)



def check(input_file, log_file, ext):

    samples = get_download_samples(input_file, ext)

    s = open(log_file).read()

    lines = s.split('\n')

    sample_info = dict()

    max_sample_lenght = 0
    for index, line in enumerate(lines):

        if not line.startswith('----------------------------------------'):
            continue

        try:
            name = lines[index+1][4:]

            if ':' in name:
                _, name = name.split(':')

            sample_info[name] = {
                'name':       name,
                'total':      int(lines[index+2].split(':')[1].strip()), # total
                'downloaded': int(lines[index+3].split(':')[1].strip()), # downloaded
                'local':      int(lines[index+4].split(':')[1].strip()), # local
                'error':      int(lines[index+5].split(':')[1].strip()), # error
                }
        except:
            print('Error: %s' % line)

        if len(name) > max_sample_lenght:
            max_sample_lenght = len(name)


    errors = []
    empty  = []

    s = {
        'total': 0,
        'downloaded': 0, 
        'local': 0,
        'error': 0,
        }

    print ''
    print 'rucio summary:'
    print '--------------'
    for name in samples:

        if name in sample_info:
            d = sample_info[name]
        else:
            d = {
                'name': name,
                'total': 0,
                'downloaded': 0, 
                'local': 0,
                'error': 1,
            }

        if d['error'] > 0 or d['local'] + d['downloaded'] < d['total']:
            errors.append(d)

        if d['total'] == 0:
            empty.append(d)

        ss = '{name: <%s}: total={total:<3}, downloaded={downloaded: <3}, local={local: <3}, error={error: <3}' % max_sample_lenght

        print(ss.format(**d))

        s['total']      += d['total']
        s['downloaded'] += d['downloaded']
        s['local']      += d['local']
        s['error']      += d['error']


    print('> Summary:')
    ss = 'Total = {total:<3}, Downloaded = {downloaded: <3}, Local = {local: <3}, Error = {error: <3}'
    print(ss.format(**s))


    if errors:
        print('> The following samples have some errors:')
        for e in errors:
            print('\033[0;31m%s\033[0m' % e['name'])
    else:
        print('\033[0;32m> No errors\033[0m')

    if empty:
        print('> The following samples are empty:')
        for e in empty:
            print('\033[0;31m%s\033[0m' % e['name'])
    else:
        print('\033[0;32m> No empty samples\033[0m')




if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='ruciodw')

    parser.add_argument('filepath', nargs='?')
    parser.add_argument('--ext', default='', help='Extension')
    parser.add_argument('--check', action='store_true')

    if len(sys.argv) < 2:
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()


    input_file = args.filepath
    log_file = input_file + '.log'


    if not args.check:
        os.system('voms-proxy-init -voms atlas')

        try:
            download(input_file, log_file, args.ext)
        except KeyboardInterrupt:
            raise

    if os.path.isfile(log_file):
        check(input_file, log_file, args.ext)





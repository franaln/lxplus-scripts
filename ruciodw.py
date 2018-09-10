#! /usr/bin/env python

# ruciodw.py
# download, using rucio, all the samples from the input txt file

import os
import sys

if len(sys.argv) < 2:
    print("usage: ruciodw.py [file-with-samples-to-download]")
    sys.exit(1)

input_file = sys.argv[1]

log_file = input_file + '.log'

os.system('rm -f %s' % log_file)

for line in open(input_file).read().split('\n'):

    if not line or line.startswith('#'):
        continue

    
    print('> Downloading: %s' % line)
    
    cmd = 'rucio download %s | tee -a %s' % (line, log_file)

    try:
        os.system(cmd)
    except KeyboardInterrupt:
        raise



s = open(log_file).read()

lines = s.split('\n')

sample_info = []

max_sample_lenght = 0
for index, line in enumerate(lines):

    if not line.startswith('----------------------------------------'):
        continue
    
    try:
        d = {
            'name':       lines[index+1][4:],
            'total':      int(lines[index+2].split(':')[1].strip()),
            'downloaded': int(lines[index+3].split(':')[1].strip()),
            'local':      int(lines[index+4].split(':')[1].strip()),
            'error':      int(lines[index+5].split(':')[1].strip()),
            }
    except:
        print('Error: %s' % line)

    if len(d['name']) > max_sample_lenght:
        max_sample_lenght = len(d['name'])

    sample_info.append(d)


errors = []
empty  = []

print ''
print 'rucio summary:'
print '--------------'
for d in sample_info:
    if d['error'] > 0 or d['local'] + d['downloaded'] < d['total']:
        errors.append(d)

    if d['total'] == 0:
        empty.append(d)

    ss = '{name: <%s}: total={total:<3}, downloaded={downloaded: <3}, local={local: <3}, error={error: <3}' % max_sample_lenght

    print(ss.format(**d))

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





#! /usr/bin/env python

import sys

s = open(sys.argv[1]).read()

lines = s.split('\n')

sample_info = []

max_sample_lenght = 0
for index, line in enumerate(lines):

    if not line.startswith('----------------------------------------'):
        continue
    
    try:
        d = {
            'name': lines[index+1][4:],
            'total':  int(lines[index+2].split(':')[1].strip()),
            'downloaded': int(lines[index+3].split(':')[1].strip()),
            'local': int(lines[index+4].split(':')[1].strip()),
            'error': int(lines[index+5].split(':')[1].strip()),
            }
    except:
        raise        

    if len(d['name']) > max_sample_lenght:
        max_sample_lenght = len(d['name'])

    sample_info.append(d)


errors = []
empty  = []

print 'rucio summary:'
for d in sample_info:
    if d['error'] > 0 or d['local'] + d['downloaded'] < d['total']:
        errors.append(d)

    if d['total'] == 0:
        empty.append(d)

    ss = '{name: <%s}: total={total:<3}, downloaded={downloaded: <3}, local={local: <3}, error={error: <3}' % max_sample_lenght

    print ss.format(**d)

if errors:
    print '# the following samples have some errors:'
    for e in errors:
        print e['name']
else:
    print '# no errors'

if empty:
    print '# the following samples are empty:'
    for e in empty:
        print e['name']
else:
    print '# no empty samples'



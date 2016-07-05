import sys

s = open(sys.argv[1]).read()

lines = s.split('\n')

sample_info = []

max_sample_lenght = 0
for index, line in enumerate(lines):

    if not line.startswith('----------------------------------------'):
        continue
        
    d = {
        'name': lines[index+1][4:],
        'total':  int(lines[index+2].split(':')[1].strip()),
        'downloaded': int(lines[index+3].split(':')[1].strip()),
        'local': int(lines[index+4].split(':')[1].strip()),
        'error': int(lines[index+5].split(':')[1].strip()),
        }

    if len(d['name']) > max_sample_lenght:
        max_sample_lenght = len(d['name'])

    sample_info.append(d)


errors = []

print 'rucio summary:'
for d in sample_info:
    if d['error'] > 0:
        errors.append(d)

    ss = '{name: <%s}: total={total:<3}, downloaded={downloaded: <3}, local={local: <3}, error={error: <3}' % max_sample_lenght

    print ss.format(**d)

if errors:
    print '# the following samples have some errors:'
    for e in errors:
        print e['name']
else:
    print '# no errors'


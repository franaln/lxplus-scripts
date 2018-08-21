#! /usr/bin/env python

# rucio_download.py
# download, using rucio, all the samples from the input txt file

import os
import sys

if len(sys.argv) < 2:
    print("usage: rucio_download.py [file-with-samples-to-download]")
    sys.exit(1)

input_file = sys.argv[1]

log_file = input_file + '.log'

os.system('rm -f %s' % log_file)

for line in open(input_file).read().split('\n'):

    if not line or line.startswith('#'):
        continue

    
    print('# Downloading: %s' % line)
    
    cmd = 'rucio download %s | tee -a %s' % (line, log_file)

    try:
        os.system(cmd)
    except KeyboardInterrupt:
        raise

print('# Done. Check the logfile using "rucio_check.py" to verify if all samples where downloaded correctly.')



#! /usr/bin/env python

import os
import sys
import json
import argparse
import subprocess

def usage(name=None):
    return '''bigpanda.py
-----------

Download jobs info from BigPanda:

    bigpanda.py --download -u USERNAME [-o jobs.json] [-f filter] [-d days]

Print (filter/sort) jobs:

    bigpanda.py --print [-o jobs.json] [--taskname XXX] [--status done] [--sort taskname]
'''

parser = argparse.ArgumentParser(description='Show jobs from bigpanda', usage=usage())

parser.add_argument('-o', dest='jobs_file', default='jobs.json',  help='Jobs file (default: jobs.json)')
parser.add_argument('-d', '--download', dest='download_jobs', action='store_true', help='Download jobs from bigpanda')
parser.add_argument('-p', '--print', dest='print_jobs', action='store_true', help='Show jobs from bigpanda')

# Bigpanda download
parser.add_argument('-u', dest='username', default=os.environ['USER'], help='Username')
parser.add_argument('-f', dest='download_filter', help='Download only tasks with name matching this (default: user.USERNAME.*)')
parser.add_argument('--days', dest='days_filter', default='7', help='Download tasks for the last X days (default: 7)')

# Filter
parser.add_argument('-i', '--taskid',   dest='taskid',   help='Filter by taskid')
parser.add_argument('-n', '--taskname', dest='taskname', help='Filter by taskname')
parser.add_argument('-s', '--status',   dest='status',   help='Filter by status')

# Sort
parser.add_argument('--sort', dest='sort', default='jeditaskid',  help='Sort by taskname/status (default: jeditaskid)')

# Other options
parser.add_argument('--all',   dest='show_all', action='store_true', help='Show the full job dict')
parser.add_argument('--quiet', dest='show_taskname_only', action='store_true', help='Show taskname only')
parser.add_argument('--full',  dest='show_full_stats', action='store_true', help='Show full stats for matching jobs')

parser.add_argument('--retry',  dest='retry', action='store_true', help='')


args = parser.parse_args()

if not args.download_jobs and not args.print_jobs:
    print(usage())
    sys.exit(0)


jobs_file = args.jobs_file

# Dowload jobs
if args.download_jobs:

    if os.path.isfile(jobs_file):
        os.system('rm %s' % jobs_file)

    in_lxplus = ('HOSTNAME' in os.environ and '.cern.ch' in os.environ['HOSTNAME'])

    # Download cookie
    if in_lxplus:
        cmd1 = 'cern-get-sso-cookie -u https://bigpanda.cern.ch/ -o bigpanda.cookie.txt;'
    else:
        cmd1 = 'ssh {USERNAME}@lxplus.cern.ch "cern-get-sso-cookie -u https://bigpanda.cern.ch/ -o bigpanda.cookie.txt;"'.format(USERNAME=args.username)

    os.system(cmd1)


    # Download jobs data
    filter_str = 'user.%s*' % args.username if args.download_filter is None else args.download_filter
    if in_lxplus:
        cmd2 = 'curl --progress-bar -b ~/bigpanda.cookie.txt -H \'Accept: application/json\' -H \'Content-Type: application/json\' "https://bigpanda.cern.ch/tasks/?taskname={0}&days={1}&json"'.format(filter_str, args.days_filter)
    else:
        cmd2 = 'ssh {0}@lxplus.cern.ch "curl -b ~/bigpanda.cookie.txt -H \'Accept: application/json\' -H \'Content-Type: application/json\' "https://bigpanda.cern.ch/tasks/?taskname={1}&days={2}\&json""'.format(args.username, filter_str, args.days_filter)

    output = subprocess.check_output(cmd2, shell=True)

    if not isinstance(output, str):
        output = output.decode("utf-8")

    with open(jobs_file, 'w') as f:
        f.write(output)




# Show jobs
def print_job(j):

    dsinfo = j['dsinfo']

    nfiles = dsinfo['nfiles']
    nfiles_failed = dsinfo['nfilesfailed']
    nfiles_finished = dsinfo['nfilesfinished']

    job_text = '{0: <10} {1: <125} {2: <15} {3: >5}/{4: >5}'.format(j['jeditaskid'], j['taskname'], j['status'], nfiles_finished, nfiles)

    if int(nfiles_failed) > 0:
        job_text += ' (failed: {0: >5})'.format(nfiles_failed)

    if j['status'] == 'done':
        print('\033[0;32m%s\033[0m' % job_text)
    elif int(nfiles_failed) > 0:
        print('\033[0;31m%s\033[0m' % job_text)
    else:
        print(job_text)


def print_full_stats(jobs):

    total_nfiles = 0
    total_nfiles_finished = 0
    total_nfiles_failed = 0
    for j in jobs:

        dsinfo = j['dsinfo']

        total_nfiles += int(dsinfo['nfiles'])
        total_nfiles_failed += int(dsinfo['nfilesfailed'])
        total_nfiles_finished += int(dsinfo['nfilesfinished'])


    if int(total_nfiles) == 0:
        return

    perc_finished = 100*total_nfiles_finished/float(total_nfiles)
    perc_failed   = 100*total_nfiles_failed/float(total_nfiles)

    text = 'Full stats >    %i Tasks |  %.2f%% failed | %.2f%% finished' % (len(jobs), perc_failed, perc_finished)
    status = 'done' if (total_nfiles == total_nfiles_finished and total_nfiles_failed == 0) else 'running'

    job_text = '{0: <136} {1: <15} {2: >5}/{3: >5}'.format(text, status, total_nfiles_finished, total_nfiles)

    if int(total_nfiles_failed) > 0:
        job_text += ' (failed: {0: >5})'.format(total_nfiles_failed)


    print('-'*165)
    if status == 'done':
        print('\033[0;32m%s\033[0m' % job_text)
    elif int(total_nfiles_failed) > 0:
        print('\033[0;31m%s\033[0m' % job_text)
    else:
        print(job_text)


if args.print_jobs:

    with open(jobs_file) as f:

        jobs = json.load(f)

        # Filter task name
        if args.taskname is not None:
            if '&' in args.taskname:
                filter_taskname = args.taskname.split('&')
                jobs = [ j for j in jobs if all([ taskname in j['taskname'] for taskname in filter_taskname ]) ]
            elif  '|' in args.taskname:
                filter_taskname = args.taskname.split('|')
                jobs = [ j for j in jobs if any([ taskname in j['taskname'] for taskname in filter_taskname ]) ]
            else:
                jobs = [ j for j in jobs if args.taskname in j['taskname'] ]
            

        # Filter status
        if args.status is not None:
            if '&' in args.status:
                filter_status = args.status.split('&')
                jobs = [ j for j in jobs if all([ status in j['status'] for status in filter_status ]) ]
            elif  '|' in args.status:
                filter_status = args.status.split('|')
                jobs = [ j for j in jobs if any([ status in j['status'] for status in filter_status ]) ]
            else:
                jobs = [ j for j in jobs if args.status in j['status'] ]

        # Filter taksID
        if args.taskid is not None:
            jobs = [ j for j in jobs if args.taskid == str(j['jeditaskid']) ]


        # Show jobs
        for j in sorted(jobs, key=lambda t: t[args.sort]):
            if args.show_all:
                print(j)
            elif args.show_taskname_only:
                print(j['taskname'])
            else:
                print_job(j)

        if args.show_full_stats:
            print_full_stats(jobs)

        if args.retry:
            cmd = 'pbook -c "sync()"'
            os.system(cmd)

            for j in jobs:
                cmd = 'pbook -c "retry(%i)"' % j['jeditaskid']
                os.system(cmd)
            

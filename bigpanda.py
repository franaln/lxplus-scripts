#! /usr/bin/env python

# not using f-strings yet as this need to be run sometimes with python<3.6 in lxplus

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime

def usage(name=None):
    return '''bigpanda.py
-----------

Download usage:

    bigpanda.py -d [-u USERNAME] [-o jobs.json] [-f "user.username.*"] [--days days]

Print/Filter/Sort usage:

    bigpanda.py [-o jobs.json] [-n|--taskname XXX] [-s|--status done] [--sort taskname]
'''

parser = argparse.ArgumentParser(description='Show jobs from bigpanda', usage=usage())

parser.add_argument('-o', dest='jobs_file', help='Jobs file (default: ~/jobs.json)')

# Bigpanda download
parser.add_argument('-d', '--download', dest='download_jobs', action='store_true', help='Force download of jobs information from bigpanda')
parser.add_argument('-u', dest='username', default=os.environ['USER'], help='Username (default: $USER)')
parser.add_argument('-f', dest='download_filter', help='Download only tasks with name matching this (default: user.USERNAME.*)')
parser.add_argument('--days', dest='days_filter', default='15', help='Download tasks for the last X days (default: 15)')

# Filter
parser.add_argument('--db', dest='use_existing_db', action='store_true', help='Use existing db')
parser.add_argument('-i', '--taskid',   dest='taskid',   help='Filter by taskid')
parser.add_argument('-n', '--taskname', dest='taskname', help='Filter by taskname')
parser.add_argument('-s', '--status',   dest='status',   help='Filter by status')
parser.add_argument('--invtaskname', dest='invtaskname', help='')

# Sort
parser.add_argument('--sort', dest='sort', default='jeditaskid',  help='Sort by taskname/status (default: jeditaskid)')

# Other options
parser.add_argument('--all',   dest='show_all', action='store_true', help='Show the full job dict')
parser.add_argument('--stats',  dest='show_full_stats', action='store_true', help='Show full stats for matching jobs')

## pbook
parser.add_argument('--retry',  dest='retry', action='store_true', help='Retry selected jobs using pbook')
parser.add_argument('--kill',  dest='kill', action='store_true', help='Kill selected jobs using pbook')

## for download
parser.add_argument('--dw', dest='download_list', action='store_true', help='Show taskname only')
parser.add_argument('--ext', dest='output_extension', help='Add extension to taskname (for download file)')
parser.add_argument('--list',  dest='show_list', action='store_true', help='Show id lists')

# Others
parser.add_argument('--links', dest='show_links', action='store_true', help='Show bigpanda links')
parser.add_argument('--ib',  dest='ignore_broken', action='store_true', help='Don\'t show broken jobs')


args = parser.parse_args()


# ----
# Config
cookie_file = os.path.expanduser('~/.bigpanda_cookie.txt')
jobs_file   = os.path.expanduser('~/.bigpanda_jobs.json') if args.jobs_file is None else args.jobs_file

status_running = [
    'running',
    'pending',
]

redownload_time_sec = 900 # 15m
# ----

# Dowload jobs
need_download = False
if args.download_jobs or not os.path.isfile(jobs_file):
    need_download = True
elif args.use_existing_db:
    need_download = False
else:
    jobs_file_old = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(jobs_file))).total_seconds()
    if jobs_file_old > redownload_time_sec:
        need_download = True


if need_download:

    in_lxplus = ('HOSTNAME' in os.environ and '.cern.ch' in os.environ['HOSTNAME'])

    # Download cookie
    if not in_lxplus:
        os.system('ssh {USERNAME}@lxplus.cern.ch "cern-get-sso-cookie -u https://bigpanda.cern.ch/ -o {COOKIE_FILE};"'.format(USERNAME=args.username, COOKIE_FILE=cookie_file))
    elif not os.path.isfile('bigpanda.cookie.txt'):
        os.system('cern-get-sso-cookie -u https://bigpanda.cern.ch/ -o {COOKIE_FILE};'.format(COOKIE_FILE=cookie_file))

    # Download jobs data
    filter_str = 'user.%s*' % args.username if args.download_filter is None else args.download_filter
    if in_lxplus:
        cmd2 = 'curl --progress-bar -b {COOKIE_FILE} -H \'Accept: application/json\' -H \'Content-Type: application/json\' "https://bigpanda.cern.ch/tasks/?taskname={TASK}&days={DAYS}&json"'.format(COOKIE_FILE=cookie_file, TASK=filter_str, DAYS=args.days_filter)
    else:
        cmd2 = 'ssh {USER}@lxplus.cern.ch "curl -b {COOKIE_FILE} -H \'Accept: application/json\' -H \'Content-Type: application/json\' "https://bigpanda.cern.ch/tasks/?taskname={TASK}&days={DAYS}\&json""'.format(USER=args.username, COOKIE_FILE=cookie_file, TASK=filter_str, DAYS=args.days_filter)

    output = subprocess.check_output(cmd2, shell=True)

    if not isinstance(output, str):
        output = output.decode("utf-8")

    with open(jobs_file, 'w') as f:
        f.write(output)



# Show jobs
def filter_jobs(jobs, key, exp):

    fjobs = []
    if '&' in exp:
        filter_exp = exp.split('&&') if '&&' in exp else exp.split('&')
        for j in jobs:
            fcond = []
            for s in filter_exp:
                if s.startswith('~') or s.startswith('!'):
                    fcond.append(s[1:].strip() not in j[key])
                else:
                    fcond.append(s.strip() in j[key])

            if all(fcond):
                fjobs.append(j)

    elif '|' in exp:
        filter_exp = exp.split('||') if '||' in exp else exp.split('|')
        for j in jobs:
            fcond = []
            for s in filter_exp:
                if s.startswith('~') or s.startswith('!'):
                    fcond.append(s[1:].strip() not in j[key])
                else:
                    fcond.append(s.strip() in j[key])

            if any(fcond):
                fjobs.append(j)

    elif exp.startswith('~'):
        filter_exp_not = exp[1:]
        fjobs = [ j for j in jobs if filter_exp_not not in j[key] ]

    else:
        fjobs = [ j for j in jobs if exp in j[key] ]

    return fjobs


def print_job(j, show_link=False):

    dsinfo = j['dsinfo']

    nfiles = dsinfo['nfiles']
    nfiles_failed = dsinfo['nfilesfailed']
    nfiles_finished = dsinfo['nfilesfinished']

    jname = j['taskname']
    if jname.endswith('/'):
        jname = jname[:-1]

    job_text = '{0: <10} {1: <110} {2: <12} {3: >5}/{4: >5}'.format(j['jeditaskid'], jname, j['status'], nfiles_finished, nfiles)

    if show_link:
        job_text = 'https://bigpanda.cern.ch/task/%s' % job_text

    if int(nfiles_failed) > 0:
        job_text += ' (failed: {0: >5})'.format(nfiles_failed)

    if j['status'] == 'done':
        print('\033[0;32m%s\033[0m' % job_text)
    elif int(nfiles_failed) > 0 and j['status'] in status_running:
        print('\033[0;33m%s\033[0m' % job_text)
    elif int(nfiles_failed) > 0:
        print('\033[0;31m%s\033[0m' % job_text)
    else:
        print(job_text)


def print_full_stats(jobs):

    total_nfiles = 0
    total_nfiles_finished = 0
    total_nfiles_failed = 0

    jobs_done     = 0
    jobs_running  = 0
    jobs_finished = 0
    jobs_broken   = 0
    jobs_failed   = 0

    njobs = { 'done': 0, 'running': 0, 'finished':0, 'broken': 0, 'failed': 0, 'other': 0 }

    for j in jobs:

        if j['status'] in status_running:
            njobs['running'] += 1
        elif j['status'] in njobs:
            njobs[j['status']] += 1
        else:
            njobs['other'] += 1

        dsinfo = j['dsinfo']

        total_nfiles += int(dsinfo['nfiles'])
        total_nfiles_failed += int(dsinfo['nfilesfailed'])
        total_nfiles_finished += int(dsinfo['nfilesfinished'])

    if int(total_nfiles) == 0:
        return

    perc_finished = 100 * total_nfiles_finished / float(total_nfiles)
    perc_failed   = 100 * total_nfiles_failed   / float(total_nfiles)

    text = 'Stats  >   %i Jobs | %i running | %i broken | %i failed | %i finished | %i done || Files: %.1f%% failed | %.1f%% finished' % (len(jobs), njobs['running'], njobs['broken'], njobs['failed'], njobs['finished'], njobs['done'], perc_failed, perc_finished)

    if (total_nfiles == total_nfiles_finished and total_nfiles_failed == 0):
        overall_status = 'done'
    elif total_nfiles == total_nfiles_finished + total_nfiles_failed:
        overall_status = 'failed'
    else:
        overall_status = 'running'

    job_text = '{0: <121} {1: <12} {2: >5}/{3: >5}'.format(text, overall_status, total_nfiles_finished, total_nfiles)

    if int(total_nfiles_failed) > 0:
        job_text += ' (failed: {0: >5})'.format(total_nfiles_failed)

    print('-'*163)
    if overall_status == 'done':
        print('\033[0;32m%s\033[0m' % job_text)
    elif int(total_nfiles_failed) > 0 and overall_status == 'running':
        print('\033[0;33m%s\033[0m' % job_text)
    elif int(total_nfiles_failed) > 0:
        print('\033[0;31m%s\033[0m' % job_text)
    else:
        print(job_text)


# Print jobs

jobs = json.load(open(jobs_file))

# Filter broken jobs if requested
if args.ignore_broken:
    jobs = [ j for j in jobs if j['status'] == 'broken' ]

# Filter task name
if args.taskname is not None:
    jobs = filter_jobs(jobs, 'taskname', args.taskname)

# Filter status
if args.status is not None:
    jobs = filter_jobs(jobs, 'status', args.status)

# Filter taksID
if args.taskid is not None:
        jobs = [ j for j in jobs if args.taskid == str(j['jeditaskid']) ]

# Sort jobs
jobs = sorted(jobs, key=lambda t: t[args.sort])

# Show jobs
if args.show_list:
    print('[%s]' % ', '.join(['%s' % j['jeditaskid'] for j in jobs]))
else:
    for j in jobs:
        if args.show_all:
            print(j)
        elif args.download_list:
            task_name = j['taskname']
            if task_name.endswith('/'):
                task_name = task_name[:-1]
            if args.output_extension:
                task_name = task_name + args.output_extension

            if j['status'] == 'done':
                print(task_name)
            else:
                print('# (%s) %s' % (j['status'], task_name))

        else:
            print_job(j, args.show_links)

    if args.show_full_stats:
        print_full_stats(jobs)


# Use pbook to kill or retry (not need to sync now, it seems now is working but ...)
if args.retry or args.kill:

    if not jobs:
        print('No job selected, exiting ...')
        sys.exit(1)

    if args.retry:
        print('Filtering jobs with status "finished" or "failed" to retry')
        jobs = filter_jobs(jobs, 'status', 'finished|failed')

    if args.retry:
        pbook_cmd = 'retry'
    elif args.kill:
        pbook_cmd = 'kill'

    job_id_list = ','.join(['%s' % j['jeditaskid'] for j in jobs])

    py_cmd = 'for j in [%s]: %s(j)' % (job_id_list, pbook_cmd)

    cmd = 'pbook -c "%s"' % py_cmd
    os.system(cmd)

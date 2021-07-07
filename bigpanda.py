#! /usr/bin/env python

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
parser.add_argument('--mask',  dest='mask', action='store_true', help='Mask selected jobs to not show anymore (useful for broken jobs)')

args = parser.parse_args()



cookie_file = os.path.expanduser('~/.bigpanda.cookie.txt')
jobs_file = os.path.expanduser('~/.jobs.json') if args.jobs_file is None else args.jobs_file
jobs_masked_file = os.path.expanduser('~/.jobs_masked.txt')


# Dowload jobs
need_download = False
if args.download_jobs or not os.path.isfile(jobs_file):
    need_download = True
elif args.use_existing_db:
    need_download = False
else:
    jobs_file_old = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(jobs_file))).total_seconds()
    if jobs_file_old > 900:
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
    if '&&' in exp:
        filter_exp = exp.split('&&')
        for j in jobs:
            fcond = []
            for s in filter_exp:
                if s.startswith('~'):
                    fcond.append(s[1:].strip() not in j[key])
                else:
                    fcond.append(s[1:].strip() in j[key])

            if all(fcond):
                fjobs.append(j)

    elif  '||' in exp:
        filter_exp = exp.split('||')
        for j in jobs:
            fcond = []
            for s in filter_exp:
                if s.startswith('~'):
                    fcond.append(s[1:].strip() not in j[key])
                else:
                    fcond.append(s[1:].strip() in j[key])

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

    if show_link:
        job_text = 'https://bigpanda.cern.ch/task/{0: <10} {1: <110} {2: <12} {3: >5}/{4: >5}'.format(j['jeditaskid'], j['taskname'], j['status'], nfiles_finished, nfiles)
    else:
        job_text = '{0: <10} {1: <110} {2: <12} {3: >5}/{4: >5}'.format(j['jeditaskid'], j['taskname'], j['status'], nfiles_finished, nfiles)

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

    jobs_done     = 0
    jobs_running  = 0
    jobs_finished = 0
    jobs_broken   = 0
    jobs_failed   = 0
    for j in jobs:

        status = j['status']
        if status == 'done':
            jobs_done += 1
        elif status == 'running':
            jobs_running += 1
        elif status == 'finished':
            jobs_finished += 1
        elif status == 'broken':
            jobs_broken += 1
        elif status == 'failed':
            jobs_failed += 1

        dsinfo = j['dsinfo']

        total_nfiles += int(dsinfo['nfiles'])
        total_nfiles_failed += int(dsinfo['nfilesfailed'])
        total_nfiles_finished += int(dsinfo['nfilesfinished'])

    if int(total_nfiles) == 0:
        return

    perc_finished = 100*total_nfiles_finished/float(total_nfiles)
    perc_failed   = 100*total_nfiles_failed/float(total_nfiles)

    text = 'Stats  >   %i Jobs | %i running | %i broken | %i failed | %i finished | %i done || Files: %.2f%% failed | %.2f%% finished' % (len(jobs), jobs_running, jobs_broken, jobs_failed, jobs_finished, jobs_done, perc_failed, perc_finished)
    status = 'done' if (total_nfiles == total_nfiles_finished and total_nfiles_failed == 0) else 'running'

    job_text = '{0: <121} {1: <12} {2: >5}/{3: >5}'.format(text, status, total_nfiles_finished, total_nfiles)

    if int(total_nfiles_failed) > 0:
        job_text += ' (failed: {0: >5})'.format(total_nfiles_failed)

    print('-'*163)
    if status == 'done':
        print('\033[0;32m%s\033[0m' % job_text)
    elif int(total_nfiles_failed) > 0:
        print('\033[0;31m%s\033[0m' % job_text)
    else:
        print(job_text)


# Print jobs
masked_jobs = []
if os.path.isfile(jobs_masked_file):
    with open(jobs_masked_file) as f:
        lines  = f.read().split('\n')
        for line in lines:
            if line:
                masked_jobs.append(int(line))


with open(jobs_file) as f:

    jobs = json.load(f)

    # Filter masked jobs
    jobs = [ j for j in jobs if j['jeditaskid'] not in masked_jobs ]

    # Filter task name
    if args.taskname is not None:
        jobs = filter_jobs(jobs, 'taskname', args.taskname)

    # Filter status
    if args.status is not None:
        jobs = filter_jobs(jobs, 'status', args.status)

    # Filter taksID
    if args.taskid is not None:
        jobs = [ j for j in jobs if args.taskid == str(j['jeditaskid']) ]

    # Show jobs
    jobs = sorted(jobs, key=lambda t: t[args.sort])

    if args.mask and jobs:
        print('Masking the following files:')
        
        with open(jobs_masked_file, 'a+') as f:
            for j in jobs:
                f.write('%i\n' % j['jeditaskid'])

    if args.show_list:
        print('[%s]' % ', '.join(['%s' % j['jeditaskid'] for j in jobs]))
    else:
        for j in jobs:
            if args.show_all:
                print(j)
            elif args.download_list:
                task_name = j['taskname']
                if args.output_extension:
                    if task_name.endswith('/'):
                        task_name = task_name[:-1]
                    task_name = task_name + args.output_extension

                if j['status'] == 'done':
                    print(task_name)
                else:
                    print('# (%s) %s' % (j['status'], task_name))

            else:
                print_job(j, args.show_links)

        if args.show_full_stats:
            print_full_stats(jobs)




    # Use pbook to kill or retry (not working now  :/)
    if args.retry or args.kill:
        cmd = 'pbook -c "sync()"'
        os.system(cmd)

    if args.retry:
        for j in jobs:
            cmd = 'pbook -c "retry(%i)"' % j['jeditaskid']
            os.system(cmd)

    if args.kill:
        for j in jobs:
            cmd = 'pbook -c "kill(%i)"' % j['jeditaskid']
            os.system(cmd)

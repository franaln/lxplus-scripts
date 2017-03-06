#! /usr/bin/env python

import os
import sys
import re
import argparse
import datetime

# your www path (change it to your own www path!)
www_path = os.path.expanduser('~/work/www')

# public directory
public_dir = os.path.join(www_path, 'public')

username = os.environ['USER']

today = datetime.datetime.today()
daytag = today.strftime('%Y%b%d')

def publink(fpath):

    dir_ = '%s/%s' % (public_dir, daytag)

    if not os.path.isdir(dir_):
        os.system('mkdir %s' % dir_)

    if os.path.isfile(fpath):

        # basename with the extension
        fname = os.path.basename(fpath)

        # copy file to public dir
        newname = fname
        cmd = 'cp "%s" "%s/%s"' % (fpath, dir_, newname)
        os.system(cmd)

        # also save png version
        if args.index:
            pngname = fname.replace(fname[-4:], '.png')
            cmd = 'convert "%s" "%s/%s"' % (fpath, dir_, pngname)
            os.system(cmd)

        print 'https://%s.web.cern.ch/%s/public/%s/%s' % (username, username, daytag, newname) 
    
    elif os.path.isdir(fpath):

        newname = os.path.basename(fpath)

        os.system('rm -Rf "%s/%s"' % (dir_, newname))
        os.system('cp -R "%s" "%s/%s"' % (fpath, dir_, newname))

        print 'https://%s.web.cern.ch/%s/public/%s/%s' % (username, username, daytag, newname) 
    
    else: 
        print 'publink: ignoring %s' % fpath
    


def create_index(files):

    index_html = """<!DOCTYPE html>
<html>
<head>
    <title> public </title>
    <meta charset=\"utf-8\" />
    <meta http-equiv=\"content-type\" content=\"text/html; charset=UTF-8\" />
</head>

<body>
    <header class=\"clearfix page\">
        <span class=\"title\">  </span>
    </header>
""" 

    index_html += """
<center>
<table>
"""

    for f in files:

        index_html += '<tr>\n'

        plot_path = f
        png_path  = f.replace(f[-3:], 'png')

        index_html += '<td><a href=\"' + plot_path + '\"><img src=\"' + png_path + '\" width=\"800\"></a></td>\n'

        index_html += '</tr>\n'
                
    index_html += "</table>\n</center>\n"

    index_html += """
    </body>
</html>
"""

    index_path = '%s/index_test.html' % public_dir

    with open(index_path, 'w') as f:
        f.write(index_html)

    print 'https://%s.web.cern.ch/%s/public/index_test.html' % (username, username) 
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='publink (pl)')
    
    parser.add_argument('files', nargs='+')
    parser.add_argument('--index', action='store_true', help='make index')
    
    args = parser.parse_args()

    if len(args.files) < 1:
        parser.print_usage()

    for f in args.files:
        publink(f)

    if args.index:
        create_index(args.files)
        

    # import time
    # time.sleep(1)
    # elif select.select([sys.stdin,],[],[],0.0)[0]:

    #     image = re.compile(ur'Info in <TCanvas::Print>: (.*) file (.*) has been created')

    #     #print sys.stdin.read().split('\n')
    #     for line in sys.stdin.read().split('\n'):

    #         if not line:
    #             continue

    #         match = re.search(image, line)

    #         if match:
    #             publink(match.group(2))




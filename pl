#! /usr/bin/env python

import os
import sys
import re
import glob
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
        www_dir = '%s/%s' % (dir_, newname)

        cmd = 'cp "%s" "%s"' % (fpath, www_dir)
        os.system(cmd)

        # # also save png version
        # if args.index:
        #     pngname = fname.replace(fname[-4:], '.png')
        #     cmd = 'convert "%s" "%s/%s"' % (fpath, dir_, pngname)
        #     os.system(cmd)
        # else:
        print('https://%s.web.cern.ch/%s/public/%s/%s' % (username, username, daytag, newname))
    
    elif os.path.isdir(fpath):

        if fpath.endswith('/'):
            fpath = fpath[:-1]

        newname = os.path.basename(fpath)

        www_dir = '%s/%s' % (dir_, newname)

        os.system('rm -Rf "%s"' % www_dir)
        os.system('cp -R "%s" "%s"' % (fpath, www_dir))

        # also save png version
        if args.index:
            
            all_pdfs = glob.glob(www_dir+'/*.pdf')
            for pdf in all_pdfs:
                png = pdf.replace('.pdf', '.png')
                os.system('rm -f %s' % png)
                cmd = 'convert -background white -trim -gravity center -density 300 "%s" "%s"' % (pdf, png)
                os.system(cmd)

            index_path = '%s/index.html' % www_dir

            create_index([ os.path.basename(pdf) for pdf in all_pdfs ], www_dir, index_path)

            print('https://%s.web.cern.ch/%s/public/%s/%s/index.html' % (username, username, daytag, newname))
    
        else:
            print('https://%s.web.cern.ch/%s/public/%s/%s' % (username, username, daytag, newname))

    else: 
        print('publink: ignoring %s' % fpath)
    


def create_index(pdf_files, output_dir, index_path):

    width = 0.9 * 100/float(args.cols)

    index_html = """<!DOCTYPE html>
<html>
<head>
    <title>  </title>
    <meta charset=\"utf-8\" />
    <meta http-equiv=\"content-type\" content=\"text/html; charset=UTF-8\" />
    <style>
       .column {
         float: left;
         width: %.2f%%;
         padding: 5px;
       }

       .row::after {
         content: "";
         clear: both;
         display: table;
       }      
    </style>
</head>

<body>
    <header class=\"clearfix page\">
        <span class=\"title\">  </span>
    </header>
""" % width


    chunks = [pdf_files[x:x+args.cols] for x in xrange(0, len(pdf_files), args.cols)]

    for plots in sorted(chunks):

        #index_html += '<tr>\n'
        index_html += '<div class="row">\n'

        for plot in plots:

            plot_path = plot
            png_path  = plot.replace('.pdf', '.png')

            #index_html += '<td><a href=\"' + plot_path + '\"><img src=\"' + png_path + '\" width=\"500\"></a></td>\n'

            index_html += '<div class="column">\n'
            index_html += '    <a href=\"' + plot_path + '\"><img src=\"' + png_path + '\" style=\"width:100%\"></a>\n'
            index_html += '</div>\n'

        #index_html += '</tr>\n'
        index_html += '</div>\n'
                
    #index_html += "</table>\n"

    index_html += """
    </body>
</html>
"""

    with open(index_path, 'w') as f:
        f.write(index_html)

    

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='publink (pl)')
    
    parser.add_argument('files', nargs='+')
    parser.add_argument('--index', action='store_true', help='Make and index for the input directory')
    parser.add_argument('--cols', type=int, default=2, help='Number of columns')

    global args
    args = parser.parse_args()

    if len(args.files) < 1:
        parser.print_usage()

    for f in args.files:
        publink(f)






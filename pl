#! /usr/bin/env python

import os
import sys
import re
import select

# your www path (change it to your own www path!)
www_path = os.path.expanduser('/work/www')

# public directory
public_dir = os.path.join(www_path, 'public')

username = os.environ['USER']

def publink(fpath):

    if os.path.isfile(fpath):

        # basename with the extension
        fname = os.path.basename(fpath)
        
        # copy file to public dir (if .eps convert it to .png)
        if fname[-4:] == ".eps":
            newname = fname.replace('.eps', '.png')
            cmd = 'convert "%s" "%s/%s"' % (fpath, public_dir, newname)
            #os.system(cmd)
        else:
            newname = fname
            cmd = 'cp "%s" "%s/%s"' % (fpath, public_dir, newname)
            #os.system(cmd)

        print 'https://%s.web.cern.ch/%s/public/%s' % (username, username, newname) 
    
    elif os.path.isdir(fpath):

        newname = os.path.basename(fpath)

        # os.system('rm -Rf "%s/%s"' % (public_dir, newname))
        # os.system('cp -R "%s" "%s/%s"' % (fpath, public_dir, newname))

        print 'https://%s.web.cern.ch/%s/public/%s' % (username, username, newname) 
    
    else: 
        print 'publink: ignoring %s' % fpath
    



if __name__ == "__main__":


    if len(sys.argv) > 2:

        for i in len(sys.argv[1:]):
            publink(sys.argv[i])

    import time
    time.sleep(1)
    elif select.select([sys.stdin,],[],[],0.0)[0]:

        image = re.compile(ur'Info in <TCanvas::Print>: (.*) file (.*) has been created')

        #print sys.stdin.read().split('\n')
        for line in sys.stdin.read().split('\n'):

            if not line:
                continue

            match = re.search(image, line)

            if match:
                publink(match.group(2))


    else:
        print "usage: publink [file|dir]"




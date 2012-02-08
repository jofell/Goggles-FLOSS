#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright (C) 2010 GSyC/LibreSoft, Universidad Rey Juan Carlos
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Author : Roberto Calvo Palomino <rocapal__at__libresoft__dot__es>
#

import sys
import os
import mutex

from twisted.internet import reactor
from twisted.web.soap import Proxy
from multiprocessing import Process


def callback_query (value):
    reactor.stop()
    
def callback(value):
    reactor.stop()

def errback(error):
    print 'error', error
    reactor.stop()


def remote_call (json):
    proxy.callRemote('add_photo', json).addCallbacks(callback, errback)
    reactor.run()

if len(sys.argv) < 4:
    print "Usage: %s <URL> <OPTIONS> \n" %(sys.argv[0])
    print "Options:"
    print "   -a <add_options> \t add photos"
    print "      -f <file_json> \t specified the JSON file"
    print "      -d <path> \t specified the images directory"
    print "\n"
    print "   -q <file> \t send query file"
    print "   -g <file> \t generate the image index"
    print "\n"
    exit(-1) 

url = sys.argv[1]
option = sys.argv[2]
path = None

proxy = Proxy(url)

if (option == "-a"):
    suboption = sys.argv[3]
    path = sys.argv[4]
    
    if (suboption == "-f"):
        f = open(path, 'r')
        json = f.read()
        f.close()
        
        proxy.callRemote('add_photo', json).addCallbacks(callback, errback)
        reactor.run()
        
    elif (suboption == "-d"):
    
        ls = os.listdir(path)
        c=0
        
        for file_name in ls:
            
            f = open ("./add_photo_template.json","r")
            content = f.read()
            f.close()
            content_json = (content.replace("$ID_PHOTO",str(c))).replace("$PATH_PHOTO",path+file_name)      
            
            print "Sending photo '%s' ... " % (file_name)
    
            p = Process (target=remote_call, args=(content_json,))
            p.start()
            p.join()        
            
            c=c+1
            
    else:
        print "Option '%s' not recognized!" % (option)
        exit(-1) 
    
elif (option == "-q" ):
    path = sys.argv[3]
    
    f = open(path, 'r')
    json = f.read()
    f.close()
    
    proxy.callRemote('query_photo', json).addCallbacks(callback_query, errback)
    reactor.run()
    
    
elif (option == "-g" ):
    
    path = sys.argv[3]
    
    f = open(path, 'r')
    json = f.read()
    f.close()
    
    proxy.callRemote('generate_index', json).addCallbacks(callback, errback)
    reactor.run()
    
else:
    print "Option '%s' not recognized!" % (option)
    exit(-1) 
    






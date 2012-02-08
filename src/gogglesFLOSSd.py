#!/usr/bin/python
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


from FlannManager import *
from parser.json import *

import sys
import time
import os

from twisted.application import service, internet
from twisted.internet import defer
from twisted.web import server, soap


#if __name__ == '__main__':
    
#    imagesPath = "/home/rocapal/libresoft/social-network/private/work/feature-detection/python/images/fotos_500/"
#    
#    ls = os.listdir(imagesPath)
    
#    fm = FlannManager()
#    c = 0
#    for image in ls:
#        fm.add_photo(c,imagesPath + image)
#        c=c+1
#    
#    fm.create_index()
#    
#    fm.console()
    

class gogglesFLOSSdSOAP(soap.SOAPPublisher):
    
    def __init__(self):
        None
        self.fm = fm = FlannManager()
        
   # SOAP Methods
    def soap_add_photo(self, json):
        """
        Request to add_photo

        @param json: JSON stream which describes the info about add photo
        @type json: C{str}

        @return: result of the request
        @rtype: C{twisted.internet.defer.Deferred}
        """
    
        ret, data =  json_parser(json)
        
        if (ret):       
            if (data[0] == "1"):
                return self.fm.add_photo(int(data[1]),data[2])
            else:
                return False
        else:
            return False
        
    
    def soap_query_photo (self, json):
        
        ret, data =  json_parser(json)
        
        if (ret):
            if (data[0] == "2"):
                print data[2]
                return self.fm.query(data[2])
            else:
                return False
        else:
            return False
        
    def soap_generate_index (self,json):
        
        ret, data = json_parser(json)
        if (ret):
            if (data[0] == "0"):
                self.fm.create_index()
            else:
                return False
        else:
            return False    
        
    
class gogglesFLOSSd(service.MultiService):
    
    def __init__(self):
        print 'Initializing gogglesFLOSSd  ...'  
        
        self.__initialize_net_services("0.0.0.0", 9085)
        
    def __initialize_net_services(self, host, port):
        """
        Initializes the network services.

        By default, initializes a SOAP server that will listen
        on C{host} a C{port}.
        """
        service.MultiService.__init__(self)

        # Initializing SOAP Service
        #self.logger.msg('gogglesFLOSSd', INFO, 'Initializing SOAP service')
        print '[gogglesFLOSSd] - Initializing SOAP service'

        site = server.Site(gogglesFLOSSdSOAP())
        backlog = 5

        internet.TCPServer(port, site, backlog, host).setServiceParent(self)

       # self.logger.msg('gogglesFLOSSd', INFO, 'SOAP service initialized')
        print '[gogglesFLOSSd] - SOAP service initialized'
  
    
    
# Twisted loading system
# Please read the Twisted 'Using Application' HOWTO for details.
application = service.Application('gogglesFLOSSd')
gogglesFLOSSd().setServiceParent(application)    

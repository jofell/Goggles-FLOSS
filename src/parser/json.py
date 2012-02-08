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

import simplejson


def json_parser (json_data):
    """
    Parser the json file

    @param json: JSON stream which describes the info about the command
    @type json: C{str}

    @return: the command in True|False, (command, id_photo, url_photo)
    @rtype: 
    """   
    
    res = simplejson.loads(json_data)
    
    command = res['command']
    
    if command['id'] == "1":
        command_data = command['params']
        id_photo = command_data['id_photo']
        path_photo = command_data['path_photo']
        return True, (command['id'],id_photo, path_photo)        
    
    elif command['id'] == "2":
        
        command_data = command['params']
        id_photo = 0
        path_photo = command_data['path_photo']
        return True, (command['id'],id_photo, path_photo)
    
    elif command['id'] == "0":
        return True, (command['id'],0,0)
        
    else:
        print "Error: %s value not recognize as command code" % (command['id'])
        return False, ("-1",-1,-1)


    
    
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2010  GSyC/LibreSoft Group
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors: Santiago Dueñas <sduenas@libresoft.es>
#

"""
Logging module

@var LOGGER_ID: Default Blackbird's logger identifier.
@type LOGGER_ID: C{str}
@var LOG_FORMAT: Default format for log messages.
@type LOG_FORMAT: C{str}
"""

import datetime
import logging
import logging.handlers
import sys
import traceback
from threading import RLock

from twisted.python import log

from common import DEBUG, INFO, WARNING, ERROR, CRITICAL
from configuration import *

LOGGER_ID = 'Blackbird'
LOG_FORMAT = '[%(asctime)s - %(thread)d - %(levelname)s] %(message)s'


class IOLogError(Exception):
    """
    Exception raised for I/O logging errors.

    @param msg: explanation of the error
    @type msg: C{str}
    """
    def __init__(self, msg):
        self.msg = msg
    
    def __str__(self):
        return repr(self.msg)


class Logger(log.PythonLoggingObserver):
    """
    Blackbird logging system.

    Singleton class for logging messages from other Blackbird
    components. This class combines both Twisted and Python standard
    library logging APIs using an observer.
    """
    def __init__(self):
        try:
            log.PythonLoggingObserver.__init__(self, LOGGER_ID)

            cfg = get_global_config()

            self.lock = RLock()
            self.logger = logging.getLogger(LOGGER_ID)
            self.logger.setLevel(cfg.get(CFG_LOG_LEVEL))

            handler = logging.handlers.RotatingFileHandler(cfg.get(CFG_LOG),
                                                           maxBytes=cfg.get(CFG_LOG_MAX_SIZE),
                                                           backupCount=cfg.get(CFG_LOG_MAX_FILES))
            formatter = logging.Formatter(LOG_FORMAT)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        except IOError, e:
            raise IOLogError('I/O Logging error. %s' % e)
        except:
            raise

    def start(self):
        """
        Start logging message system.

        @raise IOLogError: If fails starting the logger.
        """
        try:
            self.lock.acquire()
            log.PythonLoggingObserver.start(self)
            self.lock.release()
        except Exception, e:
            self.lock.release()
            raise IOLogError('Unexpected error starting logging. %s %s' 
                             % (sys.exc_info()[0], e))

    def stop(self):
        """
        Stop logging message system.

        @raise IOLogError: If fails closing the logger.
        """
        try:
            self.lock.acquire()
            log.PythonLoggingObserver.close(self)
            self.lock.release()
        except Exception, e:
            self.lock.release()
            raise IOLogError('Unexpected error stopping logging. %s %s' 
                             % (sys.exc_info()[0], e))

    def msg(self, component, level, msg):
        """
        Log a message.

        @param component: name of the module from the logging call was
         issued
        @type component: C{str}
        @param level: Log level
        @type level: C{LOG_LEVELS}
        @param msg: message to log
        @type msg: C{str}

        @raise IOLogError: If fails logging the message.
        """
        s = '[' + component + '] ' + msg
        
        try:
            self.lock.acquire()
            log.msg(s, logLevel=level)
            self.lock.release()
        except Exception, e:
            self.lock.release()
            raise IOLogError('Cannot write in logger. %s %s' % (sys.exc_info()[0], e))
    
    def err(self, component, msg, exception=None):
        """
        Log an error.

        If X{exception} is not C{None}, the logged message will contain
        the X{traceback} of this exception.

        @param component: name of module from the logging call was
         issued
        @type component: C{str}
        @param msg: message to log
        @type msg: C{str}
        @param exception: raised exception
        @type exception: C{Exception}

        @raise IOLogError: If fails logging the message.
        """
        try:
            self.lock.acquire()
            
            msg_error = '[' + component + '] ' + msg
            if exception:
                msg_error += '\n%s' % traceback.format_exc()
                log.err(_stuff=exception, _why=msg_error)
            else:
                log.msg(msg_error, logLevel=ERROR)
            self.lock.release()
        except Exception, e:
            self.lock.release()
            raise IOLogError('Cannot write in logger. %s %s' % (sys.exc_info()[0], e))

# Logger instance
_logger = None

def get_logger():
    """
    Return the instance of the L{Logger} object.
    If the instance has not been created yet, this function creates one
    and initializes it.

    @return: Logger instance
    @rtype: L{Logger}

    @raise IOLogError: Raised when errors occur
     attempting to initialize the logging system.
    """
    global _logger

    if _logger is None:
        _logger = Logger()

    return _logger
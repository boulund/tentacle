#  Copyright (C) 2014  Fredrik Boulund and Anders Sjögren
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
import argparse
import os
import random
import uuid
from os import path
from sys import stdout, maxint
import logging
__all__ = list()


unique_logger_id = 0
__all__.append("create_file_logger")
def create_file_logger(logLevel, logNoStdout, logfile):
    """ Set logger basic config and start logging.
    """

    configFormat = "%(asctime)s: %(levelname)-8s: %(message)s" 
    formatter = logging.Formatter(configFormat)
    dateFormat = "%Y-%m-%d %H:%M:%S"

    logLevel = logLevel.lower()
    if logLevel in ("debug", "verbose"):
        logLevel = logging.DEBUG
    elif logLevel in ("info", "default"):
        logLevel = logging.INFO
    elif logLevel == "critical":
        logLevel = logging.CRITICAL

    # Get a new unique_logger_id to ask for, forcing a new logger to be returned
    # We really just want a new instance, not reuse an old one, since a new file is to be created.   
    logger = logging.getLogger(os.path.basename(logfile))
    logger.setLevel(logLevel)

    print "Creating logger with id {} writing to file {}".format(unique_logger_id, logfile)
    # Create FileHandler to log to logfile
    fh = logging.FileHandler(logfile)
    fh.setFormatter(formatter)
    fh.setLevel(logLevel)
    # Create StreamHandler to log modify format of stdout-output
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(logLevel)
    # Add the handlers to the Tentacle logger
    logger.addHandler(fh)
    if not logNoStdout:
        logger.addHandler(ch)

    logger.info(" ----- ===== LOGGING STARTED ===== ----- ")
    return logger


def create_std_logger():
    """ Create the standard logger. """
    return logger


__all__.append("LoggerProvider")
class LoggerProvider(object):
    @classmethod
    def create_argparser(cls):
        parser = argparse.ArgumentParser(add_help=False)
        log_group = parser.add_argument_group("Logging options")
        log_group.add_argument("--logLevel", dest="logLevel", type=str, default="INFO", 
            help="Specify logging level using either 'default', 'INFO', 'DEBUG', or 'CRITICAL'. [default: %(default)s]")
        log_group.add_argument("--logNoStdout", action="store_true", default=False,
            help="Developer option used to supress log output to stdout during unittests. [default: %(default)s]")
        parser.add_argument_group(log_group)
        return parser
        
    @classmethod 
    def create_from_parsed_args(cls, parsed_args, base_dir_path):
        return cls(base_dir_path=base_dir_path, logLevel=parsed_args.logLevel, logNoStdout=parsed_args.logNoStdout )
    
    def __init__(self, base_dir_path, logLevel, logNoStdout):
        self.base_dir_path = base_dir_path
        self.logLevel = logLevel
        self.logNoStdout = logNoStdout
    
    def _setup_directory_structure(self, hierarchy):
        #create any dirs
        curr_dir_path = self.base_dir_path
        for d in hierarchy:
            curr_dir_path = path.join(curr_dir_path, d)
            try:
                os.mkdir(curr_dir_path)
            except OSError, e:
                if not e.errno == 17:
                    raise
            if not path.isdir(curr_dir_path):
                os.mkdir(curr_dir_path)
        return curr_dir_path
    
    def get_logger(self, filename, hierarchy=None):
        d = self._setup_directory_structure(hierarchy or [])
        random_UUID_suffix = str(uuid.uuid4())
        file_path = path.join(d, filename+"_"+random_UUID_suffix+".log") 
        return create_file_logger(self.logLevel, self.logNoStdout, file_path)
    
    
__all__.append("get_std_logger")
_std_logger=None
def get_std_logger():
    global _std_logger
    if not _std_logger:
        _std_logger = create_std_logger()
    return _std_logger


def format_dict(d,adjust):
    s = ""
    format_string = "{:>"+str(adjust)+"}: {}\n"
    for k, v in d.iteritems():
        s = "".join([s, format_string.format(k, v)]) 
    return s   


__all__.append("print_run_settings")
def print_run_settings(options, logger):
    """ Prints the current run settings to log
    """
    logger.info("The program was run with the following settings:\n{}\n".format(format_dict(options.__dict__, 35)))


__all__.append("print_files_settings")
def print_files_settings(files, logger):
    logger.info("Processing the following files:\n{}\n".format(format_dict(files._asdict(), 15)))

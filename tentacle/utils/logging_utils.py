import argparse
import os
import random
from os import path
from sys import stdout, maxint
import logging
__all__ = list()


unique_logger_id = 0
__all__.append("create_file_logger")
def create_file_logger(verbose, logfile):
    """
    Set logger basic config and start logging
    """

    configFormat = "%(asctime)s: %(levelname)s: %(message)s" 
    dateFormat = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(configFormat=configFormat,
                        dateFormat=dateFormat,
                        level=logging.DEBUG if verbose else logging.INFO,
                        stream=stdout)

    #Get a new unique_logger_id to ask for, forcing a new logger to be returned
    #We really just want a new instance, not reuse an old one, since a new file is to be created.   
    logger = logging.getLogger(os.path.basename(logfile))

    print "Creating logger with id {} writing to file {}".format(unique_logger_id, logfile)
    # Create streamhandler to log to stdout as well as file
    ch = logging.FileHandler(logfile)
    # Set a better configFormat for console display
    formatter = logging.Formatter(configFormat)
    ch.setFormatter(formatter)
    # Add the handler to the Tentacle logger
    logger.addHandler(ch)

    logger.info(" ----- ===== LOGGING STARTED ===== ----- ")
    return logger


def create_std_logger():
    # create logger
    logger = logging.getLogger('std')
    return logger


__all__.append("LoggerProvider")
class LoggerProvider(object):
    @classmethod
    def create_argparser(cls):
        parser = argparse.ArgumentParser(add_help=False)
        log_group = parser.add_argument_group("Logging options")
        log_group.add_argument("-v", "--verbose", "--logdebug", dest="logdebug", action="store_true", default=False,
            help="Set the logging level to DEBUG (i.e. verbose), default level is INFO. No other levels available")
        parser.add_argument_group(log_group)
        return parser
        
    @classmethod 
    def create_from_parsed_args(cls, parsed_args, base_dir_path):
        return cls(base_dir_path=base_dir_path, logdebug=parsed_args.logdebug)
    
    def __init__(self, base_dir_path, logdebug):
        self.base_dir_path = base_dir_path
        self.logdebug = logdebug
    
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
        file_path = path.join(d, filename+"_"+str(random.randint(0, maxint))+".log") #TODO: fix uniqueness in a better way
        return create_file_logger(self.logdebug, file_path)
    
    
__all__.append("get_std_logger")
_std_logger=None
def get_std_logger():
    global _std_logger
    if not _std_logger:
        _std_logger = create_std_logger()
    return _std_logger


def format_dict(d):
    s = ""
    for k, v in d.iteritems():
        s = "".join([s, "{:>25}: {}\n".format(k.upper(), v)]) 
    return s   


__all__.append("print_run_settings")
def print_run_settings(options, logger):
    """
    Prints the settings used for the current run to log
    """
    logger.info("The program was run with the following settings:\n{}\n".format(format_dict(options.__dict__)))


__all__.append("print_files_settings")
def print_files_settings(files, logger):
    logger.info("Processing the following files:\n{}\n".format(format_dict(files._asdict())))

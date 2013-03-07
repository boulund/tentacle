import os
from sys import stdout
import logging
__all__ = list()

unique_logger_id = 0;
__all__.append("create_file_logger")
def create_file_logger(verbose, logfile):
    """
    Set logger basic config and start logging
    """

    configFormat = "%(asctime)s: %(message)s" #"%(asctime)s %(levelname)s: %(message)s"
    dateFormat = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(configFormat=configFormat,
                        dateFormat=dateFormat,
                        level=logging.DEBUG if verbose else logging.INFO,
                        stream=stdout)

    #Get a new unique_logger_id to ask for, forcing a new logger to be returned
    #Ww really just want a new instance, not reuse an old one, since a new file is to be created.   
    logger = logging.getLogger(os.path.basename(logfile))

    print "Creating logger with id {} writing to file {}".format(unique_logger_id, logfile)
    # Create streamhandler to log to stdout as well as file
    ch = logging.FileHandler(logfile)
    # Set a better configFormat for console display
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    ch.setFormatter(formatter)
    # Add the handler to the Tentacle logger
    logger.addHandler(ch)

    logger.info(" ----- ===== LOGGING STARTED ===== ----- ")
    return logger


def create_std_logger():
    # create logger
    logger = logging.getLogger('std')
    return logger
    
    
__all__.append("get_std_logger")
_std_logger=None
def get_std_logger():
    if not _std_logger:
        global _std_logger
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

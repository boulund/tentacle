import os, logging
from sys import stdout

def fmt(in_str):
    in_str.format(**globals())


def printer(msg):
    def p():
        print msg
    return p


def resolve_executable(program):
    #inspired by http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
    import platform
    
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    
    dirs = [s.strip('"') for s in os.environ["PATH"].split(os.pathsep)]
    current_file_dir = os.path.dirname(os.path.realpath(__file__)) 
    dirs.append(os.path.join(current_file_dir,"dependencies","bin",platform.system())) #e.g. SOMEDIR/dependencies/bin/Linux
    valids = filter(is_exe,[os.path.join(path, program) for path in dirs])
    if valids:
        return valids[0]
    return None


unique_logger_id = 0;
def start_logging(verbose, logfile):
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


def format_dict(d):
    s = ""
    for k, v in d.iteritems():
        s = "".join([s, "{:>25}: {}\n".format(k.upper(), v)]) 
    return s   


def print_run_settings(options, logger):
    """
    Prints the settings used for the current run to log
    """
    logger.info("The program was run with the following settings:\n{}\n".format(format_dict(options.__dict__)))


def print_files_settings(files, logger):
    logger.info("Processing the following files:\n{}\n".format(format_dict(files._asdict())))


def assert_file_exists(fileDesc, fileName):
    if not os.path.isfile(fileName):
        print "ERROR: " + fileDesc.capitalize() + " file not supplied correctly ("+ fileName +")."
        exit(1) 

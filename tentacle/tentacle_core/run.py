#!/usr/bin/env python

def run(argv):
    from .. import utils
    from ..utils.logging_utils import create_file_logger
    from core import TentacleCore

    files, options = TentacleCore.parse_args(argv)

    # Instantiate a logger that writes to both stdout and logfile
    # This logger is available globally after its creation
    logger = utils.create_file_logger(options.logdebug, files.log)

    utils.print_run_settings(options, logger)
    utils.print_files_settings(files, logger)

    executor = TentacleCore(logger)
    executor.analyse(files, options)
    
    
###################
#
# MAIN
#
###################
if __name__ == "__main__":
    import sys       
    run(sys.argv)
    exit(0)
#!/usr/bin/env python

def run(argv):
    from ..utils.logging_utils import create_file_logger, print_run_settings, print_files_settings
    from core import TentacleCore

    files, options = TentacleCore.parse_args(argv)

    # Instantiate a logger that writes to both stdout and logfile
    logger = create_file_logger(options.logdebug, files.log)

    # Notify user if no mapper was selected!
    if not options.pblat and not options.blast and not options.razers3:
        logger.error("No mapper selected! Need one of pblat, blast or razers3.")
        exit(1)
            
    print_run_settings(options, logger)
    print_files_settings(files, logger)

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

from ..tentacle_core import TentacleCore
from .. import utils

__all__ = ["TentacleWorker"]

class TentacleWorker():
    def __init__(self, logger_provider, options):
        self.options = options
        
    def process(self, task):  
        (core_name, files) = task
        print "---Starting work on {}, logging to {}---".format(core_name, files.log)
        # Instantiate a logger that writes to both stdout and logfile
        # This logger is available globally after its creation
        workerLogger = utils.start_logging(self.options.logdebug, files.log)
        utils.print_files_settings(files, workerLogger)
        executor = TentacleCore(workerLogger)
        executor.analyse(files, self.options)
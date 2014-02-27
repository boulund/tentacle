from ..tentacle_core import TentacleCore
from ..utils import logging_utils
import traceback

__all__ = ["TentacleWorker"]

class TentacleWorker():
    def __init__(self, parsed_args, logger_provider):
        self.logger_provider = logger_provider
        self.parsed_args = parsed_args
    
    @classmethod
    def create_from_parsed_args(cls, parsed_args, logger_provider):
        return cls(parsed_args, logger_provider)
    
    @classmethod
    def create_argparser(cls, argv):
        return TentacleCore.create_processing_argparser(argv)

    def process(self, task):  
        (core_name, files) = task
        processing_logger = self.logger_provider.get_logger(core_name, ["processing"])
        #TODO: Use logger from files
        try:
            logging_utils.print_files_settings(files, processing_logger)
            executor = TentacleCore(processing_logger)
            executor.analyse(files, self.parsed_args)
        except:
            processing_logger.error(traceback.format_exc())
            raise

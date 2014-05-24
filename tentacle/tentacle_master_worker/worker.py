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

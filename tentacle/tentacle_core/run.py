#!/usr/bin/env python
# coding: utf-8
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

def run(argv):
    from ..utils.logging_utils import create_file_logger, print_run_settings, print_files_settings
    from core import TentacleCore

    files, options = TentacleCore.parse_args(argv)

    # Instantiate a logger that writes to both stdout and logfile
    logger = create_file_logger(options.logdebug, files.log)

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

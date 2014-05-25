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
from os import path, mkdir
from os.path import isdir
import argparse

# --- Public/Exported functions and classes ---

__all__ = ["OutputDirStructure"]

class OutputDirStructure(object):
    @classmethod
    def create_argparser(cls):
        parser = argparse.ArgumentParser(add_help=False)
        general_group = parser.add_argument_group("General options", "Some options are required")
        general_group.add_argument("-o", "--outputDirectory", 
                default="tentacle_output", 
                dest='output_dir_path', 
                metavar="PATH",
                help="path to directory being created and holding the logfiles and annotations [default = %(default)s]")
        general_group.add_argument("--overwriteOutputDirectory", 
                dest="makeUniqueOutputDirectoryNameIfNeeded",
                action="store_false",
                help="If the stated outputDirectory exists, overwrite previously existing output directory [default = create new dir]")
        general_group.add_argument("--keepTempFiles",
                dest="deleteTempFiles",
                action="store_false",
                help="Remove temporary files on nodes after successful completion [default: delete]")
        return parser
        
    @classmethod
    def create_from_parsed_args(cls, options):
        return cls(output_dir_path=options.output_dir_path, makeUniqueOutputDirectoryNameIfNeeded=options.makeUniqueOutputDirectoryNameIfNeeded)
        
    def __init__(self, output_dir_path, makeUniqueOutputDirectoryNameIfNeeded):
        self.output_dir_path = path.realpath(output_dir_path)
        self.makeUniqueOutputDirectoryNameIfNeeded = makeUniqueOutputDirectoryNameIfNeeded
        self._mkdirs()
    
    @property
    def output(self):
        return self.output_dir_path
    
    @property
    def results(self):
        return path.join(self.output_dir_path, "results")
    
    @property
    def logs(self):
        return path.join(self.output_dir_path, "logs")
    
    def get_logs_subdir(self, name):
        new_dir = path.join(self.output_dir_path, "logs", name)
        if not isdir(new_dir):
            mkdir(new_dir)
        return new_dir
    
    def _create_and_adjust_output_dir(self, suffix = None):
        try:
            new_output_dir = self.output_dir_path + str(suffix or "")
            mkdir(new_output_dir)
            self.output_dir_path = new_output_dir
        except OSError as e:
            if e.errno!=17 or (not self.makeUniqueOutputDirectoryNameIfNeeded):
                raise
            new_suffix = (suffix or 1) + 1
            self._create_and_adjust_output_dir(new_suffix)

    def _mkdirs(self):
        self._create_and_adjust_output_dir()
        for d in [self.results, self.logs]:
            mkdir(d)

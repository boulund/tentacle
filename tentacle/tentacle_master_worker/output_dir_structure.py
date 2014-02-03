#!/usr/bin/env python
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
        general_group.add_argument("-o", "--outputDirectory", default="tentacle_output", dest='output_dir_path', help="path to directory being created and holding the logfiles and annotations [default =  %(default)s]")
        general_group.add_argument("--makeUniqueOutputDirectoryNameIfNeeded", action="store_true", default="False", help="If the stated outputDirectory exists, should a new unique directory name be created instead of the program failing? [default =  %(default)s]")
        general_group.add_argument("--deleteTempFiles", dest="deleteTempFiles", default=False, action="store_true", 
            help="Remove temporary files on nodes after successful completion [default: %(default)s]")
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

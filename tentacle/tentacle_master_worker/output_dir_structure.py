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
        parser.add_argument("-o", "--outputDirectory", default="tentacle_output", dest='output_dir_path', help="path to directory being created and holding the logfiles and annotations [default =  %(default)s]")
        return parser
        
    @classmethod
    def create_from_parsed_args(cls, options):
        return cls(output_dir_path=options.output_dir_path)
        
    def __init__(self, output_dir_path):
        self.output_dir_path = path.realpath(output_dir_path)
        self._mkdirs()
    
    @property
    def results(self):
        return path.join(self.output_dir_path, "results")
    
    @property
    def communication(self):
        return path.join(self.output_dir_path, "communication")

    @property
    def logs(self):
        return path.join(self.output_dir_path, "logs")
    
    def get_logs_subdir(self, name):
        new_dir = path.join(self.output_dir_path, "logs", name)
        if not isdir(new_dir):
            mkdir(new_dir)
        return new_dir

    def _mkdirs(self):
        for d in [self.results, self.communication, self.logs]:
            mkdir(d)
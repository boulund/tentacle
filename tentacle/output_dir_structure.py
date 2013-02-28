#!/usr/bin/env python
from os import path, mkdir
import argparse

# --- Public/Exported functions and classes ---

__all__ = ["OutputDirStructure"]

class OutputDirStructure(object):
    _attribute_key = "output_dir_structure"
    
    @staticmethod
    def create_argparser():
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("-o", "--outputDirectory", default="tentacle_output", dest=OutputDirStructure._attribute_key, help="path to directory being created and holding the logfiles and annotations [default =  %(default)s]")
        return parser
        
    @staticmethod
    def new_from_parsed_args(options):
        return OutputDirStructure(getattr(options,OutputDirStructure._attribute_key))
        
    def __init__(self, output_dir_path):
        self.output_dir_path = path.realpath(output_dir_path)
    
    @property
    def results(self):
        return path.join(self.output_dir_path, "results")
    
    @property
    def communication(self):
        return path.join(self.output_dir_path, "communication")

    @property
    def logs(self):
        return path.join(self.output_dir_path, "logs")
    
    @property
    def task_logs(self):
        return path.join(self.output_dir_path, "logs", "tasks")

    @property
    def worker_logs(self):
        return path.join(self.output_dir_path, "logs", "workers")

    @property
    def master_logs(self):
        return path.join(self.output_dir_path, "logs", "master")
    
    @property
    def launcher_logs(self):
        return path.join(self.output_dir_path, "logs", "launcher")
    
    @property
    def distributed_stdio(self):
        return path.join(self.output_dir_path, "logs", "distributed stdio")
    
    def mkdirs(self):
        for d in [self.results, self.communication, self.logs, self.task_logs, self.worker_logs, self.master_logs, self.launcher_logs, self.distributed_stdio]:
            mkdir(d)
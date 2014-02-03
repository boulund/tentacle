#!/usr/bin/env python
# coding: UTF-8
# Fredrik Boulund 2013
# Anders Sjögren 2013

from subprocess import PIPE#, Popen
from gevent.subprocess import Popen
from mapper import Mapper
import psutil
import os

from ..utils import resolve_executable
from ..utils import mapping_utils

__all__ = ["Pblat"]

class Pblat(Mapper):
    """
    Pblat
    """
    def __init__(self, logger, mapper="pblat"):
        self.logger = logger
        self.mapper_string = mapper
        self.mapper = resolve_executable(mapper)
        self.options = {}
        self.input_reads_format = "FASTA"

    @staticmethod
    def create_argparser():
        """
        Creates a parser for mapping options.
        """
        import argparse

        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options for pblat")
        mapping_group.add_argument("--pblatThreads", dest="pblatThreads",                 
            type=int, default=psutil.NUM_CPUS, metavar="N",                               
            help="pblat: Set number of threads for parallel blat mapping [default: N=%(default)s [=autodetected]")
        return parser
    

    def construct_mapper_call(self, local_files, output_filename, options):
        """
        Parses options and creates a mapper call (python list) that can be used
        with Popen.
        """

        mapper_call = [self.mapper,
                       "-threads=" + str(options.pblatThreads),
                       "-out=blast8" ]

        # Base the command in the result dir and give the file_name relative to that.
        result_base = os.path.dirname(output_filename)
        # Append arguments to mapper_call                                
        mapper_call.append(os.path.relpath(local_files.contigs, result_base))  
        mapper_call.append(os.path.relpath(local_files.reads, result_base))    
        mapper_call.append(os.path.relpath(output_filename, result_base))

        return mapper_call
    

    def assert_mapping_results(self, output_filename):
        """
        Makes a quick check that the mapping appears successful.
        """
        pass
        # TODO: Assert mapping results

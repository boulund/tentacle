#!/usr/bin/env python
# coding: UTF-8
# Fredrik Boulund 2013
# Anders Sjögren 2013
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

from subprocess import PIPE#, Popen
from gevent.subprocess import Popen
from mapper import Mapper
import psutil
import os

from ..utils import resolve_executable
from ..utils import mapping_utils
from ..parsers import blast8

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
        self.output_parser = blast8.parse_blast8

    @staticmethod
    def create_argparser():
        """
        Creates and returns a parser for mapping options.
        """
        import argparse

        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options for pblat")
        mapping_group.add_argument("--pblatThreads", dest="pblatThreads",                 
            type=int, default=psutil.NUM_CPUS, metavar="N",                               
            help="pblat: Set number of threads for parallel blat mapping [default: N=%(default)s (autodetected)]")
        mapping_group.add_argument("--pblatMinIdentity", type=int, default=90,
            help="pblat: minIdentity in percent [default: %(default)s]")
        mapping_group.add_argument("--pblatOther", type=str, default="",
            help="pblat: Additional commandline arguments to pblat within a quoted string [default: not used]")
        return parser
    

    def construct_mapper_call(self, local_files, options):
        """
        Parses options and creates a mapper call (python list) that can be used
        with Popen.
        """

        mapper_call = [self.mapper,
                       "-threads={}".format(options.pblatThreads),
                       "-minIdentity={}".format(options.pblatMinIdentity),
                       "-out=blast8" ]

        if options.pblatOther:
            import shlex
            otherOptions = shlex.split(options.pblatOther)
            for token in otherOptions:
                mapper_call.append(token)

        # Base the command in the result dir and give the file_name relative to that.
        output_filename = local_files.reads+".mapped"
        result_base = os.path.dirname(output_filename)

        # Append arguments to mapper_call                                
        mapper_call.append(os.path.relpath(local_files.contigs, result_base))  
        mapper_call.append(os.path.relpath(local_files.reads, result_base))    
        mapper_call.append(os.path.relpath(output_filename, result_base))

        return mapper_call, output_filename
    

    def assert_mapping_results(self, output_filename):
        """
        Makes a quick check that the mapping appears successful.
        """
        pass
        # TODO: Assert mapping results

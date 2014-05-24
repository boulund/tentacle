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

from ..utils import resolve_executable
from ..utils import mapping_utils
from ..parsers import gem

__all__ = ["Gem"]

class Gem(Mapper):
    """
    GEM
    """
    def __init__(self, logger, mapper_name):
        self.logger = logger
        self.mapper_string = mapper_name
        self.mapper = resolve_executable("gem-mapper")
        self.options = {}
        self.input_reads_format = "FASTQ"
        self.output_parser = gem.parse_gem

    @staticmethod
    def create_argparser():
        """
        Creates a parser for mapping options.
        """
        import argparse

        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options", "Options for GEM.")
        # TODO: This gemFasta thing is bugged in the modularized code.
        mapping_group.add_argument("--gemFasta", dest="gemFasta",
            default=False, action="store_true",
            help="GEM: Input files are FASTA format and not FASTQ [default %(default)s].")
        mapping_group.add_argument("--gemThreads", dest="gemThreads",
            default=psutil.NUM_CPUS, type=int, metavar="N",
            help="GEM: number of threads allowed [default: %(default)s (autodetected)]")
        mapping_group.add_argument("--gemDBName", dest="gemDBName",
            type=str, default="", metavar="DBNAME", required=True, 
            help="GEM: Name of the reference file in the database tarball (i.e. including .fasta extension). It must share basename with the rest of the DB.")
        mapping_group.add_argument("--gemm", dest="gemm",
            type=float, default=0.04, metavar="m", 
            help="GEM: max_mismatches, percent mismatches [default: %(default)s]")
        mapping_group.add_argument("--geme", dest="geme",
            type=float, default=0.04, metavar="e", 
            help="GEM: max_exit_distance, percent differences [default: %(default)s]")
        mapping_group.add_argument("--gemMinMatchedBases", dest="gemMinMatchedBases",
            type=float, default=0.80, metavar="B", 
            help="GEM: min-matched-bases, percent [default: %(default)s]")
        mapping_group.add_argument("--gemGranularity", dest="gemGranularity",
            type=int, default=2500000, metavar="G", 
            help="GEM: granularity when reading from file (in bytes) [default: %(default)s]")
        mapping_group.add_argument("--gemOther", type=str, default="",
            help="GEM: additional command line arguments to GEM [default: %(default)s]")
        
        return parser
    

    def prepare_references(self, remote_files, local_files, options, rebase_to_local_tmp):
        """
        Transfers and prepares reference DB for GEM.
        """
        mapping_utils.copy_untar_ref_db(remote_files.contigs, 
                                        local_files.contigs, 
                                        self.logger)
        return local_files._replace(contigs=rebase_to_local_tmp(options.gemDBName))


    def construct_mapper_call(self, local_files, options):
        """
        Parses options and creates a mapper call (python list) that can be used
        with Popen.
        """

        mapper_call = [self.mapper,
                       "-I", options.gemDBName.split(".",1)[0]+".gem",
                       "-i", local_files.reads, 
                       "-o", local_files.reads, #output prefix; gem appends with .map
                       "-T", str(options.gemThreads),
                       "-m", str(options.gemm),
                       "-e", str(options.geme),
                       "--min-matched-bases", str(options.gemMinMatchedBases),
                       "--granularity", str(options.gemGranularity),
                       ]

        if not options.gemFasta:
            mapper_call.append("-q")
            mapper_call.append('ignore')
        if options.gemOther:
            import shlex
            otherOptions = shlex.plit(options.gemOther)
            for token in otherOptions:
                mapper_call.append(token)

        output_filename = local_files.reads+".map"

        return mapper_call, output_filename
    

    def assert_mapping_results(self, output_filename):
        """
        Makes a quick check that the mapping appears successful.
        """
        pass
        # TODO: Assert mapping results

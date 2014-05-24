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
from ..parsers import sam

__all__ = ["Bowtie2"]

class Bowtie2(Mapper):
    """
    Bowtie2
    """
    def __init__(self, logger, mapper_name):
        self.logger = logger
        self.mapper_string = mapper_name
        self.mapper = resolve_executable(mapper_name)
        self.options = {}
        self.input_reads_format = "FASTQ"
        self.output_parser = sam.parse_sam

    @staticmethod
    def create_argparser():
        """
        Creates a parser for mapping options.
        """
        import argparse

        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options", "Options for bowtie2.")
        # TODO: The first bowtie2Fasta argument is broken in this modularized implementation
        mapping_group.add_argument("--bowtie2Fasta", dest="bowtie2Fasta",
            default=False, action="store_true",
            help="bowtie2: Input files are FASTA format and not FASTQ [default %(default)s].")
        mapping_group.add_argument("--bowtie2DBName", dest="bowtie2DBName",
            type=str, default="", metavar="DBNAME", required=True,
            help="bowtie2: Name of the FASTA file in the database tarball (including extension). It must share basename with the rest of the DB.")
        mapping_group.add_argument("--bowtie2Other", type=str, default="",
            help="bowtie2: additional command line options for bowtie2 [default: not used]")
        
        return parser
    

    def prepare_references(self, remote_files, local_files, options, rebase_to_local_tmp=None):
        """
        Transfers and prepares reference DB for Bowtie2.
        """
        mapping_utils.copy_untar_ref_db(remote_files.contigs, local_files.contigs, self.logger)
        return local_files._replace(contigs=rebase_to_local_tmp(options.bowtie2DBName))


    def construct_mapper_call(self, local_files, options):
        """
        Parses options and creates a mapper call (python list) that can be used
        with Popen.
        """

        output_filename = local_files.reads+".mapped"
        mapper_call = [self.mapper,
                       "-x", options.bowtie2DBName.split(".",1)[0],
                       "-S", output_filename,
                       "-U", local_files.reads,
                       "-p", str(options.bowtie2Threads)]

        if options.bowtie2Other:
            import shlex
            otherOptions = shlex.split(options.bowtie2Other)
            for token in otherOptions:
                mapper_call.append(token)

        return mapper_call, output_filename
    

    def assert_mapping_results(self, output_filename):
        """
        Makes a quick check that the mapping appears successful.
        """
        pass
        # TODO: Assert mapping results

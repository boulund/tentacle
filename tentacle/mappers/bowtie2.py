#!/usr/bin/env python
# coding: UTF-8
# Fredrik Boulund 2013
# Anders Sjögren 2013

from subprocess import PIPE#, Popen
from gevent.subprocess import Popen
from mapper import Mapper
import psutil

from ..utils import resolve_executable
from ..utils import mapping_utils

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
            help="bowtie2: Name of the reference file BASENAME in the database tarball (NO extension). It must have the same basename as the rest of the DB.")
        mapping_group.add_argument("--bowtie2Other", type=str, default="",
            help="bowtie2: additional command line options for bowtie2 [default: not used]")
        
        return parser
    

    def prepare_references(self, remote_files, local_files, options, rebase_to_local_tmp=None):
        """
        Transfers and prepares reference DB for Bowtie2.
        """
        mapping_utils.copy_untar_ref_db(remote_files.contigs, local_files.contigs, self.logger)
        return local_files._replace(contigs=rebase_to_local_tmp(options.bowtie2DBName))


    def construct_mapper_call(self, local_files, output_filename, options):
        """
        Parses options and creates a mapper call (python list) that can be used
        with Popen.
        """

        mapper_call = [self.mapper,
                       "-x", str(options.bowtie2DBName),
                       "-S", output_filename,
                       "-U", local_files.reads,
                       "-p", str(options.bowtie2Threads)]

        if options.bowtie2Other:
            import shlex
            otherOptions = shlex.split(options.bowtie2Other)
            for token in otherOptions:
                mapper_call.append(token)

        return mapper_call
    

    def assert_mapping_results(self, output_filename):
        """
        Makes a quick check that the mapping appears successful.
        """
        pass
        # TODO: Assert mapping results

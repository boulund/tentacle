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

__all__ = ["Blastn"]

class Blastn(Mapper):
    """
    Blast
    """
    def __init__(self, logger, mapper_name):
        self.logger = logger
        self.mapper_string = mapper_name
        self.mapper = resolve_executable(mapper_name)
        self.options = {}
        self.input_reads_format = "FASTA"

    @staticmethod
    def create_argparser():
        """
        Creates a parser for mapping options.
        """
        import argparse

        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options for blast")
        mapping_group.add_argument("--blastThreads", dest="blastThreads",
            default=psutil.NUM_CPUS, type=int, metavar="N",
            help="blast: number of threads allowed [default: %(default)s]")
        mapping_group.add_argument("--blastTask", dest="blastTask",
            default="", type=str, required=True,
            help="blast: What task to be run, refer to blast manual for available options [default: %(default)s]")
        mapping_group.add_argument("--blastDBName", dest="blastDBName",
            type=str, default="", metavar="DBNAME", required=True,
            help="blast: Name of the FASTA file in the database tarball (including extension). It must have the same basename as the rest of the DB.")

        return parser
    

    def prepare_references(self, remote_files, local_files, options, rebase_to_local_tmp=None):
        """
        Transfers and prepares reference DB for blast.
        """
        mapping_utils.copy_untar_ref_db(remote_files.contigs, local_files.contigs, self.logger)
        return local_files._replace(contigs=rebase_to_local_tmp(options.blastDBName))


    def construct_mapper_call(self, local_files, output_filename, options):
        """
        Parses options and creates a mapper call (python list) that can be used
        with Popen.
        """

        mapper_call = [self.mapper,
                       "-outfmt", "6", #blast8 tabular output
                       "-query", str(local_files.reads),
                       "-db", options.blastDBName.split(".",1)[0],
                       "-out", output_filename,
                       "-num_threads", str(options.blastThreads)]

        if options.blastTask:
            mapper_call.append("-task")
            mapper_call.append(str(options.blastTask))

        return mapper_call
    

    def assert_mapping_results(self, output_filename):
        """
        Makes a quick check that the mapping appears successful.
        """
        pass
        # TODO: Assert mapping results

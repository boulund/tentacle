#!/usr/bin/env python
# coding: UTF-8
# Fredrik Boulund 2013
# Anders Sjögren 2013

from subprocess import PIPE#, Popen
from gevent.subprocess import Popen
from mapper import Mapper

from ..utils import resolve_executable
from ..utils import mapping_utils
from ..parsers import blast8

__all__ = ["Usearch"]

class Usearch(Mapper):
    """
    USEARCH
    """
    def __init__(self, logger, mapper_name):
        self.logger = logger
        self.mapper_string = mapper_name
        self.mapper = resolve_executable(mapper_name)
        self.options = {}
        self.input_reads_format = "FASTA"
        self.output_parser = blast8.parse_blast8

    @staticmethod
    def create_argparser():
        """
        Creates a parser for mapping options.
        """
        import argparse

        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("USEARCH mapping options")
        mapping_group.add_argument("--usearchID", dest="usearchID",
            type=float, default="0.9", metavar="I",
            help="usearch: Sequence similarity for usearch_global [default: %(default)s]")
        mapping_group.add_argument("--usearchQueryCov", dest="usearchQueryCov",
            type=str, default="", metavar="COVERAGE",
            help="usearch: Query coverage in range 0.0-1.0.")
        mapping_group.add_argument("--usearchDBName", dest="usearchDBName",
            type=str, default="", metavar="DBNAME", required=True,
            help="usearch: Name of the FASTA file in the database tarball (i.e. including .fasta extension). It must share basename with the .udb in the tarball.")
        mapping_group.add_argument("--usearchStrand", dest="usearchStrand",
            type=str, default="both", metavar="S",
            help="usearch: If searching nucleotide sequences, specify either 'both' or 'plus' [default: %(default)s]")
        mapping_group.add_argument("--usearchFilterSequencesShorterThan", dest="usearchFilterSequencesShorterThan",
            type=int, default=0, metavar="L",
            help="usearch: Remove sequences that align with less than L nucleotides to a reference")
        mapping_group.add_argument("--usearchOther", dest="usearchOther",
            type=str, default="", metavar="S",
            help="usearch: Quoted string containing usearch arguments. Warning: No checks of"+\
                 " validity are made.")
        
        return parser
    

    def prepare_references(self, remote_files, local_files, options, rebase_to_local_tmp=None):
        """
        Transfers and prepares reference DB for usearch.
        """
        mapping_utils.copy_untar_ref_db(remote_files.contigs, local_files.contigs, self.logger)
        return local_files._replace(contigs=rebase_to_local_tmp(options.usearchDBName))


    def construct_mapper_call(self, local_files, options):
        """
        Parses options and creates a mapper call (python list) that can be used
        with Popen.
        """

        output_filename = local_files.reads+".mapped"
        mapper_call = [self.mapper,
                       "-usearch_global", str(local_files.reads),
                       "-db", options.usearchDBName.split(".",1)[0]+".udb",
                       "-id", str(options.usearchID),
                       "-blast6out", output_filename]

        if options.usearchQueryCov:
            mapper_call.append("-query_cov")
            mapper_call.append(str(options.usearchQueryCov))
        if options.usearchStrand:
            mapper_call.append("-strand")
            mapper_call.append(str(options.usearchStrand))
        if options.usearchOther:
            import shlex
            usearchOtherOptions = shlex.split(options.usearchOther)
            for token in usearchOtherOptions:
                mapper_call.append(token)

        return mapper_call, output_filename
    

    def assert_mapping_results(self, output_filename):
        """
        Makes a quick check that the mapping appears successful.
        """
        pass
        # TODO: Assert mapping results

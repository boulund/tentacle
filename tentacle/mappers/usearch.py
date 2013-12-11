#!/usr/bin/env python
# coding: UTF-8
# Fredrik Boulund 2013
# Anders Sjögren 2013

from subprocess import PIPE#, Popen
from gevent.subprocess import Popen
from mapper import Mapper

from ..utils import resolve_executable

__all__ = ["Usearch"]

class Usearch(Mapper):
    """
    USEARCH
    """

    def create_argparser(self):
        """
        Creates a parser for mapping options.
        """
        import argparse

        self.parser = argparse.ArgumentParser(add_help=False)
        mapping_group = self.parser.add_argument_group("USEARCH mapping options")
        mapping_group.add_argument("--usearchID", dest="usearchID",
            type=float, default="0.9", metavar="I",
            help="usearch: Sequence similarity for usearch_global [default: %(default)s]")
        mapping_group.add_argument("--usearchQueryCov", dest="usearchQueryCov",
            type=str, default="", metavar="COVERAGE",
            help="usearch: Query coverage in range 0.0-1.0.")
        mapping_group.add_argument("--usearchDBName", dest="usearchDBName",
            type=str, default="", metavar="DBNAME",
            help="usearch: Name of the FASTA file in the database tarball (including extension).")
        mapping_group.add_argument("--usearchStrand", dest="usearchStrand",
            type=str, default="", metavar="S",
            help="usearch: If searching nucleotide sequences, specify either 'both' or 'plus'")
        mapping_group.add_argument("--usearchOther", dest="usearchOther",
            type=str, default="", metavar="S",
            help="usearch: Quoted string containing usearch arguments. Warning: No checks of"+\
                 " validity are made.")


    def construct_mapper_call(self, reads, reference, outputFilename, options):
        """
        Parses options and creates a mapper call (python list) that can be used
        with Popen.
        """

        self.output_filename = outputFilename+".results"
        mapper_call = [utils.resolve_executable("usearch"),
                       "-usearch_global", str(local.reads),
                       "-db", options.usearchDBName.split(".", 1)[0]+".udb",
                       "-id", str(options.usearchID),
                       "-blast6out", output_filename]

        if options.usearchQueryCov:
            mapper_call.append("-query_cov")
            mapper_call.append(str(options.usearchQueryCov))
        if options.usearchStrand:
            mapper_call.append("-strand")
            mapper_call.append(str(options.usearchStrand))

        # Run the command in the result dir and give the file_name relative to that.
        result_base = os.path.dirname(output_filename)

        return mapper_call
    

    def assert_mapping_results(self, output_filename):
        """
        Makes a quick check that the mapping appears successful.
        """
        pass
        # TODO: Assert mapping results

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

__all__ = ["Razers3"]

class Razers3(Mapper):
    """
    RazerS3
    """
    def __init__(self, logger, mapper="razers3"):
        self.logger = logger
        self.mapper_string = mapper
        self.mapper = resolve_executable(mapper)
        self.options = {}
        self.input_reads_format = "FASTQ"

    @staticmethod
    def create_argparser():
        """
        Creates a parser for mapping options.
        """
        import argparse

        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options", "Options for Razers3.")
        mapping_group.add_argument("--r3Identity", dest="razers3Identity",
            type=int, default=95,
            help="RazerS3: Percent identity of matched reads [default: %(default)s]")
        mapping_group.add_argument("--r3Recognition", dest="razers3Recognition",
            type=int, default=100,
            help="RazerS3: Recognition rate (sensitivity) [default: %(default)s]")
        mapping_group.add_argument("--r3Max", dest="razers3Max",
            type=int, default=1,
            help="RazerS3: Max number of returned matches per read [default: %(default)s]")
        mapping_group.add_argument("--r3Swift", dest="razers3Swift", action="store_true", 
            default=False,
            help="RazerS3: Change RazerS3 from pigeonhole to swift filter. [default: pigeonhole]")
        mapping_group.add_argument("--r3Threads", dest="razers3Threads",
            type=int, default=psutil.NUM_CPUS, metavar="N",
            help="RazerS3: Number of threads for RazerS3. [default: %(default)s (autodetected)]")
        
        return parser
    

    def construct_mapper_call(self, local_files, options):
        """
        Parses options and creates a mapper call (python list) that can be used
        with Popen.
        """

        mapper_call = [self.mapper,
                       "-i", str(options.razers3Identity),
                       "-rr", str(options.razers3Recognition),
                       "-m", str(options.razers3Max),
                       "-tc", str(options.razers3Threads)]
        
        if options.razers3Swift:
            mapper_call.append("-fl")
            mapper_call.append("swift")

        # Append positional arguments
        mapper_call.append(local_files.contigs)
        mapper_call.append(local_files.reads)

        # RazerS3 automatically appends .razers to the output filename
        output_filename = local_files.reads+".razers"

        return mapper_call, output_filename
    

    def assert_mapping_results(self, output_filename):
        """
        Makes a quick check that the mapping appears successful.
        """
        pass
        # TODO: Assert mapping results

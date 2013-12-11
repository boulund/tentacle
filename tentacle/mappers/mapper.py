#!/usr/bin/env python
# coding: UTF-8
# Fredrik Boulund 2013
# Anders Sjögren 2013

from subprocess import PIPE#, Popen
from gevent.subprocess import Popen

from ..utils import resolve_executable

__all__ = ["Mapper"]

class Mapper(object):
    """
    A mapper object.
    """

    def __init__(self, mapper, logger):
        self.logger = logger
        self.mapper_string = mapper
        self.mapper = resolve_executable(mapper)
        self.parser = self.create_argparser()
        self.options = {}


    def create_argparser(self):
        """
        Initializes an argparser for arguments relevant for the mapper.
        To be expanded in a subclass.
        It is recommended to only utilize long options and prepend
        option names with the mapper to minimize risk of overloading other
        options from other argument parsers.
        """
        pass


    def construct_mapper_call(self, input, reference, outputFilename, options):
        """
        Parses options and creates a mapper call (python list) that can be used 
        with Popen. 
        To be expanded in a subclass.
        """
        pass


    def run_mapper(self, reads, reference, output_file, options):
        """
        Calls mapper with input, references, options.

        Input: 
            input           'reads'
            reference       'reference'.
            output_file     filename to write output to options         
        """

        mapper_call = self.construct_mapper_call(input.reads, input.reference, options)

        self.logger.info("Running {0}...".format(self.mapper))
        self.logger.debug("Mapper call: {0}".format(' '.join(mapper_call)))
        stdout.flush() # Force printout so users knows what's going on
        
        # Run the command in the result dir and give filenames relative to that.
        result_base_dir = os.path.dirname(self.output_filename)
        mapper_process = Popen(mapper_call, stdout=PIPE, stderr=PIPE, cwd=result_base)
        mapper_stream_data = mapper_process.communicate()

        if mapper_process.returncode is not 0:
            self.logger.error("{0}: return code {1}".format(self.mapper, mapper_process.returncode))
            self.logger.error("{0}: stdout: {1}".format(self.mapper, mapper_stream_data[0]))
            self.logger.error("{0}: stderr: {1}".format(self.mapper, mapper_stream_data[1]))
            exit(1)
        else:
            self.assert_mapping_results(output_filename)
        self.logger.debug("{0}: stdout: {1}".format(self.mapper, mapper_stream_data[0]))
        self.logger.debug("{0}: stderr: {1}".format(self.mapper, mapper_stream_data[1]))

        return output_filename


    def assert_mapping_results(self, output_filename):
        """
        Makes a quick check that the mapping appears successful.
        """
        pass
        # TODO: Assert mapping results




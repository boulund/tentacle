#!/usr/bin/env python
# coding: UTF-8
"""Generic mapping module for Tentacle.

.. moduleauthor:: Fredrik Boulund <fredrik.boulund@chalmers.se>

.. module:: mapper
   :synopsis: Generic mapping module for Tentacle.

"""

from subprocess import PIPE#, Popen
from gevent.subprocess import Popen
from sys import stdout
from collections import OrderedDict
import os

from ..utils import resolve_executable
from ..utils import mapping_utils

__all__ = ["Mapper"]

class Mapper(object):
    """
    A generic mapper class.

    The mapper class has several methods that require custom implementations
    for each specific mapper. See examples of other mapper modules that 
    subclass this class on how this can be done.

    .. note:: 
       This class must be subclassed and customized to produce a functional mapping module.
    """

    def __init__(self, logger, mapper):
        """Initalizes a mapper object.

        Args:
            logger: A logging.logger object.
            mapper (str): The executable name of the mapper.

        Returns:
            None
        
        Raises:
            ExecutableNotFound: If mapper executable is not found in sys.path.
        """
        self.logger = logger
        self.mapper_string = mapper
        self.mapper = resolve_executable(mapper)
        self.options = {}
        self.input_reads_format = "FASTA" # "FASTQ"


    @staticmethod
    def create_argparser():
        """Initializes an argparser for arguments relevant for the mapper.

        Args: 
            None

        Returns:
            parser: an initalized argparse.ArgumentParser with an argument_group
                    with options for this specific mapper.

        It is recommended to only utilize long options and prepend
        option names with the mapper to minimize risk of overloading other
        options from other argument parsers (e.g. write --blastOption
        instead of just --option if you are adding a module for BLAST).

        .. note:
           This method must be customized in a subclass.

        """
        pass


    def construct_mapper_call(self, local_files, options):
        """Parses options and creates a mapper call (python list) that can be used 
        with Popen. 

        Args:
            local_files (namedtuple): A tuple with three fields containing
                node-local filenames. Fields: 'reads', 'contigs', 'annotations'.
            options (Namespace): A Namespace from ArgpumentParser.parse_args with
                all arguments parsed from the command line (incl. non-mapper-related).

        Returns:
            mapper_call (list): A shlex.split()-style list of the mapper call.
            output_filename (str): A string with the output filename.

        .. note::
            This method must be customized in a subclass.

        For examples on how to customize this method, please refer to one 
        of the other modules available in :mod:`tentacle.mappers`.
        """
        pass

    def assert_mapping_results(self, output_filename):
        """Makes a quick check that the mapping appears successful.

        Can be used to perform a quick sanity check of the output file
        before continuing with the rest of the pipeline.

        .. note::
            This method must be customized in a subclass.
        """
        pass
        # TODO: Assert mapping results



############## NORMALLY THE FOLLOWING METHODS DO NOT NEED MODIFICATION

    def prepare_references(self, remote_files, local_files, options, rebase_to_local_tmp=None):
        """Transfers and prepares reference DB for the mapper.

        Calls :func:`tentacle.mapping_utils.gunzip_copy` to transfer the references to the 
        compute node. 

        Args:
            remote_files (namedtuple): Contains fields; 'contigs', 'reads', 'annotations'.
            local_files (namedtuple): Contains fields; 'contigs', 'reads', 'annotations'.
            options (Namespace): Parsed arguments from the Tentacle command line.

        Kwargs:
            rebase_to_local_tmp (function): An optional function, used only in special cases,
                see e.g. :mod:`tentacle.mappers.gem`. 

        Returns:
            local_files (namedtuple): Updated with new filename of transferred references.

        .. note::
            This method normally does NOT require modification.
        """
        new_contigs = mapping_utils.gunzip_copy(remote_files.contigs, local_files.contigs, self.logger)
        return local_files._replace(contigs=new_contigs)


    def prepare_reads(self, remote_files, local_files, options):
        """Transfer and prepare reads.

        Contains all logic for preparing reads, including; determining format (FASTA/FASTQ),
        detects compression (gzip), performs quality filtering (FASTX), and FASTQ-to-FASTA
        conversion (seqtk).

        Args:
            remote_files (namedtuple): Contains fields; 'contigs', 'reads', 'annotations'.
            local_files (namedtuple): Contains fields; 'contigs', 'reads', 'annotations'.
            options (Namespace): Parsed arguments from the Tentacle command line.
        Returns:
            local_files (namedtuple): Updated with new filename of the prepared reads. 
        Raises:
            PipelineError: If any part of the quality control/conversion pipeline
                malfunctions.

        .. note::
            This method normally does NOT require modification.
        """

        def check_return_code(Popen_tuple):
            """ Checks the return code of a finished Popen object."""
            Popen_object, program_name = Popen_tuple
            if Popen_object.returncode is not 0:
                self.logger.error("{0} return code {1}".format(program_name, Popen_object.returncode))
                self.logger.error("{0} stdout: {1}".format(program_name, Popen_object.stdout.read()))
                self.logger.error("{0} stderr: {1}".format(program_name, Popen_object.stderr.read()))
                raise PipelineError(program_name+" Error code: "+str(Popen_object.returncode)+" "+Popen_object.stdout.read()+"\n"+Popen_object.stderr.read())
            else:
                return

        pipeline_components = []
        reads = remote_files.reads
        destination = local_files.reads
        # Make sure any .gz filename endings get removed from the destination
        # since some mapping tools rely on file endings to determine the
        # input format
        if destination.lower().endswith((".gz")):
            destination = destination[:-3]

        self.logger.info("Preparing %s for mapping.", reads)

        # Uncompress reads into Popen PIPE object
        uncompressed_reads = mapping_utils.uncompress_into_Popen(reads, self.logger)

        # Determine reads format (FASTA or FASTQ) and return new source stream
        read_source, fastq_format = mapping_utils.determine_format(uncompressed_reads, self.logger)

        # Perform filtering and trimming if FASTQ,
        # otherwise just write to disk
        program_filter = "fastq_quality_filter"
        program_trim = "fastq_quality_trimmer"
        program_convert = "seqtk"
        if fastq_format and options.qualityControl:
            self.logger.info("Performing quality control on reads...")
            self.logger.info("Filtering reads using {}...".format(program_filter))
            filtered_reads = mapping_utils.filtered_call(self.logger,
                                    source=read_source,
                                    program=program_filter,
                                    arguments= {"-q":options.fastqMinQ,
                                                "-p":options.fastqProportion,
                                                "-v":""})
            pipeline_components.append((filtered_reads, program_filter))
            self.logger.info("Trimming reads using {}...".format(program_filter))
            trimmed_reads = mapping_utils.filtered_call(self.logger,
                                   source=filtered_reads,
                                   program=program_trim,
                                   arguments={"-t":options.fastqThreshold,
                                              "-l":options.fastqMinLength,
                                              "-v":""})
            pipeline_components.append((trimmed_reads, program_trim))
            if self.input_reads_format == "FASTA":
                self.logger.info("Converting FASTQ to FASTA using {}...".format(program_convert))
                arguments = OrderedDict([("seq", ""), 
                                         ("-A", ""), 
                                         ("-", "")])
                fasta_reads = mapping_utils.filtered_call(self.logger,
                                     source=trimmed_reads,
                                     program=program_convert,
                                     arguments=arguments)
                pipeline_components.append((fasta_reads, program_convert))
                # Some mappers require a .fasta file ending so we append that just in case
                destination = destination+".fasta"
                written_reads = mapping_utils.write_reads(fasta_reads, destination, self.logger)
            else:
                written_reads = mapping_utils.write_reads(trimmed_reads, destination, self.logger)
            pipeline_components.append((written_reads, "cat"))
        elif fastq_format and not options.qualityControl:
            if self.input_reads_format == "FASTA":
                self.logger.info("Converting FASTQ to FASTA...")
                arguments = OrderedDict([("seq", ""), ("-A", ""), ("-", "")])
                fasta_reads = mapping_utils.filtered_call(self.logger,
                                     source=read_source,
                                     program=program_convert,
                                     arguments=arguments)
                pipeline_components.append((fasta_reads, program_convert))
                # Some mappers require a .fasta file ending so we append that
                destination = destination+".fasta"
                written_reads = mapping_utils.write_reads(fasta_reads, destination, self.logger)
            else:
                written_reads = mapping_utils.write_reads(read_source, destination, self.logger)
            pipeline_components.append((written_reads, "cat"))
        else:
            if not options.qualityControl:
                self.logger.info("Skipping quality control and writing reads unmodified to local storage...")
            else:
                self.logger.info("Writing reads to local storage...")
            written_reads = mapping_utils.write_reads(read_source, destination, self.logger)
            pipeline_components.append((written_reads, "cat"))

        # Calling .communicate() on the Popen object runs 
        # the entire pipeline that has been pending
        written_reads.communicate() 
        for component in pipeline_components:
            check_return_code(component)
        self.logger.info("Read transfer completed.")
        if fastq_format and options.qualityControl:
            self.logger.info("Read quality control and FASTA conversion completed.")
            self.logger.info("Filtering statistics:\n%s", filtered_reads.stderr.read())
            self.logger.info("Trimming statistics:\n%s", trimmed_reads.stderr.read())

        if options.bowtie2FilterReads:
            # Transfer genome index for bowtie2 and perform read filtering
            db_destination = os.path.dirname(destination)+"/"+os.path.basename(options.bowtie2FilterDB)
            mapping_utils.copy_untar_ref_db(options.bowtie2FilterDB, db_destination, self.logger)
            filtered_reads = mapping_utils.filter_human_reads_bowtie2(destination, options, self.logger)
            self.logger.info("Finished preparing %s for mapping.", reads)
            return local_files._replace(reads=filtered_reads)

        self.logger.info("Finished preparing %s for mapping.", reads)
        return local_files._replace(reads=destination)



    def run_mapper(self, local_files, options):
        """Runs mapper.

        Args:
            remote_files (namedtuple): Contains fields; 'contigs', 'reads', 'annotations'.
            options (Namespace): A Namespace from ArgpumentParser.parse_args with
                all arguments parsed from the command line (incl. non-mapper-related).
        Returns:
            output_filename (str): Filename of mapping results.
        Raises:
            MapperError: If the mapper does not return with returncode 0.

        .. note::
            This method normally does NOT require modification.
        """

        mapper_call, output_filename = self.construct_mapper_call(local_files, options)

        self.logger.info("Running {0}...".format(self.mapper))
        self.logger.debug("Mapper call: {0}".format(' '.join(mapper_call)))
        stdout.flush() # Force printout so users knows what's going on
        # Run the command in the result dir and give filenames relative to that.
        result_base_dir = os.path.dirname(output_filename)
        mapper_process = Popen(mapper_call, stdout=PIPE, stderr=PIPE, cwd=result_base_dir)
        mapper_stream_data = mapper_process.communicate()

        if mapper_process.returncode is not 0:
            self.logger.error("{0}: return code {1}".format(self.mapper, mapper_process.returncode))
            self.logger.error("{0}: stdout: {1}".format(self.mapper, mapper_stream_data[0]))
            self.logger.error("{0}: stderr: {1}".format(self.mapper, mapper_stream_data[1]))
            raise MapperError("\n".join([self.mapper, 
                                         str(mapper_process.returncode), 
                                         mapper_stream_data[0],
                                         mapper_stream_data[1]]))
        else:
            self.assert_mapping_results(output_filename)
        self.logger.debug("{0}: stdout: {1}".format(self.mapper, mapper_stream_data[0]))
        self.logger.debug("{0}: stderr: {1}".format(self.mapper, mapper_stream_data[1]))

        return output_filename







class PipelineError(Exception):
    """ Default error for any read preparation related stuff """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class MapperError(Exception):
    """ Default error for any mapper related stuff """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


#!/usr/bin/env python2.7
# Fredrik Boulund 2013
# Anders Sjogren 2013

from sys import exit, stdout
from subprocess import PIPE#, Popen
from collections import namedtuple
import argparse
import os
import shutil
import tempfile

from gevent.subprocess import Popen
#import gevent
#gevent.monkey.patch_subprocess()
import psutil

import parseModule
from .. import utils

#InFiles = namedtuple("InFiles", ["contigs", "reads", "annotations"])
AllFiles = namedtuple("AllFiles", ["contigs", "reads", "annotations", "annotationStats", "log"])

class TentacleCore:
    def __init__(self, logger):
        self.logger = logger
        
    def gunzip_copy(self, source_file, destination):
        """
        Takes a source file and a destination and determines whether to 
        gunzip the file before moving it to the destination.
        """
    
        if source_file.endswith((".gz", ".GZ")):
            self.logger.info("File %s seems gzipped, uncompressing to node...", source_file)
            
            # Remove the .gz suffix and redirect stdout to this file
            destination = destination[:-3]
            outfile = open(destination, "w")
    
            gunzip_call = [utils.resolve_executable("gunzip"), source_file, "-c"]
            gunzip = Popen(gunzip_call, stdout=outfile, stderr=PIPE).communicate()
    
            outfile.close()
            if gunzip[1] != "":
                self.logger.error("Could not gunzip %s to node", source_file)
                self.logger.error("Gunzip stderr: %s", gunzip[1])
                exit(1)
            else:
                self.logger.info("Successfully gunzipped %s to node.", source_file)
        else: # It is probably not compressed (at least not with gzip)
            try:
                self.logger.info("Copying %s to node...", source_file)
                shutil.copy(source_file, destination)
                self.logger.info("Successfully copied %s to node.", source_file)
            except OSError, message:
                self.logger.error("File copy error: %s", message)
    
        return destination 
    
    
    def uncompress_into_Popen(self, filename):
        """
        Determine filetype based on file name ending and start a Popen 
        object with gunzip stream output, otherwise cat into a pipe.
        """
        
        if filename.endswith((".gz", ".GZ")):
            self.logger.info("File %s seems gzipped, uncompressing.", filename)
            gunzip_call = [utils.resolve_executable("gunzip"), "-c", filename]
            uncompressed_data = Popen(gunzip_call, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        else:
            self.logger.info("File %s does not seem gzipped.", filename)
            cat_call = [utils.resolve_executable("cat"), filename]
            uncompressed_data = Popen(cat_call, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        return uncompressed_data
    
    
    def create_new_pipe(self, firstchar, source):
        """
        Creates a new source pipe from a string and a Popen object
        """
    
        new_source = Popen([r"(printf '\x%02x' && cat)" % ord(firstchar)], 
                           shell=True, stdin=source.stdout, stdout=PIPE)
        return new_source
    
    
    def determine_format(self, source):
        """
        Reads the first byte of the stream to determine file format
        (FASTA or FASTQ) and returns a new pipe with the data along
        with a format description (True for FASTQ, False for FASTA).
        """
    
        firstchar = source.stdout.read(1)
        if firstchar == "@":
            self.logger.info("Reads appear to be in FASTQ format, performing quality control.")
            fastq = True
            new_source = self.create_new_pipe(firstchar, source)
        elif firstchar == ">":
            self.logger.info("Reads appear to be in FASTA format, skipping quality control.")
            fastq = False
            new_source = self.create_new_pipe(firstchar, source)
        else:
            self.logger.error("Reads file not in FASTQ or FASTA format")
            exit(1)
    
        return (new_source, fastq)
    
    
    def filtered_call(self, source, program, **options):
        """
        Generic filter call.
        Calls PROGRAM with OPTIONS given as keyword arguments to this function
        which are supplied as command line options to the PROGRAM.
        The function assumes the PROGRAM takes the SOURCE as input on stdin
        and returns its output on stdout.
        """
    
        filter_call = [utils.resolve_executable(program)]
        args = [str(key)+str(option) for key, option in options.iteritems()]
        filter_call.extend(args)
    
        self.logger.debug("{} call: {}".format(program, ' '.join(filter_call)))
        result = Popen(filter_call, stdin=source.stdout, stdout=PIPE, stderr=PIPE)
        return result
    
    
    def write_reads(self, source, destination):
        """
        Takes a Popen object or Pipe (multiprocessing) and writes
        its content to filename destination
        """
    
        # TODO: Create a thread that writes the source.stdout to a file
        # instead.
        destination_file = open(destination, "w")
        write = Popen([utils.resolve_executable("cat")], stdin=source.stdout, stdout=destination_file)
        return write
    
        
    def prepare_reads(self, reads, destination, options):
        """
        Takes a set of reads and prepares them for mapping on the node.
        """
    
        # Make sure any .gz filename endings get removed from the destination
        # since some mapping tools rely on file endings to determine the
        # input format
        if destination.endswith((".gz",".GZ")):
            destination = destination[:-3]
    
        self.logger.info("Preparing %s for mapping.", reads)
    
        # Uncompress reads into Popen PIPE object
        uncompressed_reads = self.uncompress_into_Popen(reads)
    
        # Determine reads format (FASTA or FASTQ) and return new source stream
        read_source, fastq_format = self.determine_format(uncompressed_reads)
    
        # Perform filtering and trimming if FASTQ, 
        # otherwise just write to disk
        if fastq_format:
            self.logger.info("Filtering reads...")
            filtered_reads = self.filtered_call(source=read_source, 
                                    program="fastq_quality_filter",
                                    **{"-q":options.fastqMinQ, 
                                       "-p":options.fastqProportion,
                                       "-v":""})
            self.logger.info("Trimming reads...")
            trimmed_reads = self.filtered_call(source=filtered_reads,
                                   program="fastq_quality_trimmer",
                                   **{"-t":options.fastqThreshold,
                                      "-l":options.fastqMinLength,
                                      "-v":""})
            if options.pblat:
                self.logger.info("Converting FASTQ to FASTA...")
                fasta_reads = self.filtered_call(source=trimmed_reads,
                                     program="fastq_to_fasta",
                                     **{"-n":"", #discards low quality reads
                                        "-v":""})
                self.logger.info("Writing filtered and trimmed reads to local storage...")
                # Append .fasta to filename since it is converted to that format
                # and pblat requires that suffix
                destination = destination+".fasta"
                written_reads = self.write_reads(fasta_reads, destination)
            else:
                self.logger.info("Writing filtered and trimmed reads to local storage...")
                written_reads = self.write_reads(trimmed_reads, destination)
            # Calling .communicate() on the Popen object runs the
            # entire pipeline that has been pending
            written_reads.communicate() # Writes to disk
            # TODO: Check returncodes of all parts of the pipeline
            self.logger.info("Read quality control and FASTA conversion completed.")
            self.logger.info("Filtering statistics:\n%s", filtered_reads.stderr.read())
            self.logger.info("Trimming statistics:\n%s", trimmed_reads.stderr.read())
            if options.pblat: self.logger.info("FASTA conversion statistics:\n%s", fasta_reads.stderr.read())
        else:
            self.logger.info("Writing reads to local storage...")
            written_reads = self.write_reads(read_source, destination)
            # Calling .communicate() on the Popen object runs the
            # entire pipeline that has been pending
            written_reads.communicate() # Writes to disk
            self.logger.info("Successfully wrote reads to local disk.")
    
        self.logger.info("Finished preparing %s for mapping.", reads)
    
        return destination
    
    def preprocess_data_and_map_reads(self, files, options):
        """
        Performs file copy operations, gunzip, quality filtering etc. 
        before running Razers3.
        """
        
        temp_dir = tempfile.mkdtemp()
        self.logger.info("Using created tempdir {} .".format(temp_dir))
    
        #remote = extract_file_options(options)
        # Define local filenames of source files
        def rebase_to_local_tmp(f):
            return os.path.join(temp_dir, os.path.basename(f))
        LocalTuple = namedtuple("local", ["contigs", "reads", "annotations"])
        local = LocalTuple(rebase_to_local_tmp(files.contigs), rebase_to_local_tmp(files.reads), rebase_to_local_tmp(files.annotations))
    
        # Copy annotation and contig files to node, returns updated local filename
        # TODO: This could be parallelized
        new_annotations = self.gunzip_copy(files.annotations, local.annotations)
        local = local._replace(annotations=new_annotations)
        new_contigs = self.gunzip_copy(files.contigs, local.contigs)
        local = local._replace(contigs=new_contigs)
    
        # Prepare reads for mapping (gunzip, filter and transfer to node)
        # Returns updated local filename
        new_reads = self.prepare_reads(files.reads, local.reads, options)
        local = local._replace(reads=new_reads)
    
        # TODO: Add mapper agnostic paired-end capabilities
        if options.pblat:
            mapper_call = [utils.resolve_executable("pblat"),
                           "-threads=" + str(options.pblatThreads),
                           "-out=blast8" ]
            
            #A workaround for pblat not working correctly with some absolute path names for the result:
            # Run the command in the result dir and give the file_name relative to that.
            mapped_reads_file_path = local.reads+".result"
            result_base = os.path.dirname(mapped_reads_file_path)

            # Append arguments to mapper_call
            mapper_call.append(os.path.relpath(local.contigs, result_base))
            mapper_call.append(os.path.relpath(local.reads, result_base))
            mapper_call.append(os.path.relpath(mapped_reads_file_path, result_base))
    
            # Run pblat
            self.logger.info("Running pblat...")
            self.logger.debug("pblat call: {0}".format(' '.join(mapper_call)))
            stdout.flush() # Force printout so user knows what's going on
            pblat = Popen(mapper_call, stdout=PIPE, stderr=PIPE, cwd=result_base)
            pblat_stream_data = pblat.communicate()
            if pblat.returncode is not 0:
                self.logger.error("pblat:\n{}".format(pblat_stream_data[1])) # [1] is stderr
                exit(1)
            else:
                # assert_mapping_results()
                pass
        else:
            mapper_call = [utils.resolve_executable("razers3"),
                           "-i", str(options.razers3Identity),
                           "-rr", str(options.razers3Recognition), 
                           "-m", str(options.razers3Max)]
            if options.razers3Swift:
                mapper_call.append("-fl")
                mapper_call.append("swift")
            # Append arguments to mapper_call
            mapper_call.append(local.contigs)
            mapper_call.append(local.reads)
    
            # Run RazerS3
            self.logger.info("Running RazerS3...")
            self.logger.debug("RazerS3 call: %s", ' '.join(mapper_call))
            stdout.flush() # Force printout so user knows what's going on
            razers3 = Popen(mapper_call, stdout=PIPE, stderr=PIPE)
            razers3_stream_data = razers3.communicate()
            if razers3.returncode is not 0:
                self.logger.error("RazerS3:\n%s", razers3_stream_data[1]) # [1] contains stderr
                exit(1)
            else:
                # TODO: Add some kind of control of results file size or 
                # contents to ensure mapping was actually successful?
                # An empty result file might be ok? 
                # Call function something like assert_mapping_results() ?
                self.logger.info("RazerS3 mapping completed.")
                if os.path.getsize(local.reads+".result") == 0: # TODO: Fix output filename
                    self.logger.warning("Mapping results are empty.")
                self.logger.debug("RazerS3 stdout:\n%s", razers3_stream_data[0])
                self.logger.debug("RazerS3 stderr:\n%s", razers3_stream_data[1])
    
        # Prepare and return a named tuple with essential information from mapping
        MappedReadsTuple = namedtuple("mapped_reads", ["contigs", "mapped_reads", "annotations"])
        mapped_reads = MappedReadsTuple(local.contigs,
                                        mapped_reads_file_path, # TODO: Fix output filename
                                        local.annotations)
        return mapped_reads
    
    
    def analyse_coverage(self, mapped_reads, outfile, options):
        """
        Analyses mapped contigs and counts map coverage
        """
    
        # Perform analysis of contigs and initialize data structure
        self.logger.info("Initializing map coverage data structure...")
        contig_coverage = parseModule.indexContigs(mapped_reads.contigs, self.logger)
        self.logger.info("Map coverage data structure initialized.")
    
        # Sum the number of mapped contigs
        self.logger.info("Summing number of mapped contigs...")
        contig_coverage = parseModule.sumMapCounts(mapped_reads.mapped_reads, 
                                                   contig_coverage, 
                                                   options.pblat,
                                                   self.logger)
        self.logger.info("Number of mapped contigs summation completed.")
    
        # DEBUG printing (EXTREMELY SLOW)
        if options.outputCoverage:
            import numpy as np
            np.set_printoptions(threshold='nan', linewidth='inf')
            self.logger.debug("Writing complete coverage maps to contigCoverage.txt... (this is sloooow!)")
            with open("contigCoverage.txt", "w") as coverageFile:
                for contig in contig_coverage.keys():
                    coverageFile.write('\t'.join([contig, str(contig_coverage[contig])+"\n"]))
            self.logger.debug("Coverage maps written to contigCoverage.txt.")
    
        # Compute counts per annotation
        self.logger.info("Computing counts per annotation, writing to {}...".format(outfile))
        parseModule.computeAnnotationCounts(mapped_reads.annotations, contig_coverage, outfile, self.logger)
        self.logger.info("Counts per annotation computation completed.")
    
        
    @staticmethod
    def create_fastq_argparser():
        """
        Creates parser for FASTQ options (used for quality filtering).
        """
        
        parser = argparse.ArgumentParser(add_help=False)
        quality_filtering_group = parser.add_argument_group("Quality filtering options", "Options for FASTQ")
        #TODO: Change dest to be the same as argument, e.g. fastqMinQ=>fqMinQuality. Will be useful when writing out config file with all options for future use with @saved-opts as argument.
        quality_filtering_group.add_argument("--fqMinQuality", dest="fastqMinQ", 
            type=int, default=10, 
            help="FASTQ filter: minimum base quality score, [default: %(default)s]")
        quality_filtering_group.add_argument("--fqProportion", dest="fastqProportion",
            type=int, default=50,
            help="FASTQ filter: minimum proportion of bases above base quality score [default: %(default)s]")
        quality_filtering_group.add_argument("--fqThreshold", dest="fastqThreshold",
            type=int, default=1, 
            help="FASTQ trim: minium quality threshold. Nucleotides with lower quality will be trimmed from the end of the sequence, [default: %(default)s]")
        quality_filtering_group.add_argument("--fqMinlength", dest="fastqMinLength",
            type=int, default=0,
            help="FASTQ trim: minimum length. Sequences shorter will be discarded [default: 0 (entire read)]")    
        return parser
    
    
    @staticmethod
    def create_razerS3_argparser():
        """
        Creates parser for RazerS3 options (used for mapping).
        """
    
        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options", "Options for RazerS3.")
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
        # TODO: Remake the implementation of paired end data to make it mapper agnostic.
        #mapping_group.add_argument("--r3Paired", dest="razers3Paired",
        #    type=str, default=False,
        #    help="RazerS3: Paired end reads file [default: not used]")
        return parser
    
    
    @staticmethod
    def create_pblat_argparser():
        """
        Creates parser for pblat options (used for mapping).
        """
    
        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options", "Options for pblat.")
        mapping_group.add_argument("--pblat", dest="pblat",
            default=False, action="store_true",
            help="pblat: Use pblat instead of RazerS3 [default: %(default)s]")
        mapping_group.add_argument("--pblatThreads", dest="pblatThreads",
            type=int, default=psutil.NUM_CPUS, metavar="N",
            help="pblat: Set number of threads for parallel blat mapping [default: N=%(default)s [=the current number of CPUs]]")
        return parser
    
    
    @staticmethod
    def create_processing_argarser():
        """
        Creates parser for options that describes HOW to process the files (not WHAT files are to be processed).
        
        Is used both for the single contig-file and many-contig-files cases.
        """
        
        parser = argparse.ArgumentParser(parents=[TentacleCore.create_fastq_argparser(), 
                                                  TentacleCore.create_razerS3_argparser(),
                                                  TentacleCore.create_pblat_argparser()], add_help=False)
     
        debug_group = parser.add_argument_group("DEBUG developer options", "Use with caution!")
        debug_group.add_argument("--outputCoverage", dest="outputCoverage", action="store_true", default=False,
            help="Outputs complete coverage information into contigCoverage.txt")
            
        return parser
    
        
    def analyse(self, files, options):
        mapped_reads = self.preprocess_data_and_map_reads(files, options)
        self.analyse_coverage(mapped_reads, files.annotationStats, options)
        self.logger.info("Results available in %s", files.annotationStats)
        self.logger.info(" ----- ===== LOGGING COMPLETED ===== ----- ")

    
    @staticmethod
    def extract_file_options(options):
        # Define original source files
        # Simple quick validity check of positional arguments.
        # RazerS3 will complain about file contents of CONTIGS and READS
        # later if they are incorrectly formatted etc.
        utils.assert_file_exists("contigs", options.contigs);
        utils.assert_file_exists("reads", options.reads);
        utils.assert_file_exists("annotations", options.annotations);
        return AllFiles(options.contigs, options.reads, options.annotations, options.annotationStatsFile, options.logfile)
    
    
    @staticmethod
    def create_single_data_argparser():
        """
        Creates parser for all arguments for when a single triplet (contigs, reads, annotions) are to be processed.
        
        Performs some rudimental file existance assertions
        """
    
        parser = argparse.ArgumentParser(description="Maps reads to annotations in contigs and produces corresponding stats.", parents=[TentacleCore.create_processing_argarser()], add_help=True)
        
        parser.add_argument("contigs", help="path to contigs file (gzippped FASTQ)")
        parser.add_argument("reads", help="path to read file (gzipped FASTQ)")
        parser.add_argument("annotations", help="path to annotation file (tab separated text)")    
        #TODO: change default tentacle.log to something like reads_filename-extensions+".tab.log"?
        parser.add_argument("-l", "--logfile", dest="logfile", default="tentacle.log",
           help="Set a different log filename. [Default: %(default)s]")
        #TODO: change default annotationStats.tab to something like reads_filename-extensions+".tab"?
        #TODO: Make dest and option have same nomenclature (e.g. --annotationStatsFile, or rather dest="output", "-o" and "--output")
        parser.add_argument("-o", "--outAnnotationCounts", dest="annotationStatsFile", 
          default="annotationStats.tab",
          help="Output filename for the counts of reads that matched to annotations [default: %(default)s]")
        
        return parser
        
        
    @staticmethod
    def parse_args(argv):
        parser = TentacleCore.create_single_data_argparser()
        options = parser.parse_args()
        files = TentacleCore.extract_file_options(options)
    
        return (files, options)


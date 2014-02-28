#!/usr/bin/env python2.7
# coding: utf-8
# Fredrik Boulund 2013
# Anders Sjögren 2013

from sys import exit, stdout
from subprocess import PIPE#, Popen
from collections import namedtuple
from time import time
import argparse
import os
import shutil
import tempfile
import pkgutil
import importlib

from gevent.subprocess import Popen
#import gevent
#gevent.monkey.patch_subprocess()
import psutil

import parseModule
from .. import utils
from ..utils import mapping_utils

#InFiles = namedtuple("InFiles", ["contigs", "reads", "annotations"])
AllFiles = namedtuple("AllFiles", ["contigs", "reads", "annotations", "annotationStats", "log"])

class TentacleCore:
    def __init__(self, logger):
        self.logger = logger

    def initalize_mapper(self, options):
        """
        Initalizes a mapper object.
        """
        mappers = importlib.import_module(".."+options.mapperName, "tentacle.mappers.subpkg")
        mapperClass = getattr(mappers, options.mapperName.title())
        mapper = mapperClass(self.logger, options.mapperName) 
        self.logger.debug("Initialized mapper {}.".format(options.mapperName))
        return mapper


    def preprocess_data_and_map_reads(self, files, options):
        """
        Performs file copy operations, gunzip, quality filtering etc. 
        before running the mapper.
        """

        mapper = self.initalize_mapper(options)
        
        temp_dir = tempfile.mkdtemp()
        self.logger.info("Created tempdir {} .".format(temp_dir))

        # Define local filenames of source files.
        def rebase_to_local_tmp(f):
            return os.path.join(temp_dir, os.path.basename(f))

        LocalTuple = namedtuple("local", ["contigs", "reads", "annotations"])
        local = LocalTuple(rebase_to_local_tmp(files.contigs), rebase_to_local_tmp(files.reads), rebase_to_local_tmp(files.annotations))
    
        # Copy annotation file to node, returns updated local filename.
        # TODO: References, Reads, and Annotations can be transferred in parallel.
        preprocess_annotation_time = time()
        new_annotations = mapping_utils.gunzip_copy(files.annotations, local.annotations, self.logger)
        local = local._replace(annotations=new_annotations)
        self.logger.info("Time to transfer and prepare annotations: %s", time()-preprocess_annotation_time)

        # Transfer and unpack references.
        # Returns mapper DB filename where relevant and specified by the correct command line flag.
        preprocess_references_time = time()
        local = mapper.prepare_references(files, local, options, rebase_to_local_tmp)
        self.logger.info("Time to transfer and prepare references: %s", time()-preprocess_references_time)
    
        # Prepare reads for mapping (gunzip, filter and transfer to node)
        # Returns updated local filename.
        reads_time = time()
        local = mapper.prepare_reads(files, local, options)
        self.logger.info("Time to transfer and preprocess reads: %s", time()-reads_time)
        
        # Map reads using mapper on node with node-local files in tempdir.
        maptime = time()
        mapped_reads_file_path = mapper.run_mapper(local, options)
        self.logger.info("Time to map reads: %s", time()-maptime)

        # Prepare and return a named tuple with essential information from mapping.
        MappedReadsTuple = namedtuple("mapped_reads", ["contigs", "mapped_reads", "annotations"])
        mapped_reads = MappedReadsTuple(local.contigs,
                                        mapped_reads_file_path, 
                                        local.annotations)
        return (mapped_reads, temp_dir)
    
    
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
                                                   options,
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


    def delete_temporary_files(self, temp_dir):
        """
        Deletes all temporary files created during analysis.
        """
        # TODO: More logic to determine if delete was actually successful etc.
        self.logger.info("Deleting temporary files in folder '{}'...".format(temp_dir))
        shutil.rmtree(temp_dir)
        self.logger.info("Successfully deleted temporary files in folder '{}'...".format(temp_dir))


    def save_mapping_results(self, mapped_reads, target_filename):
        """
        Create a compressed copy of the raw mapping results in the output directory
        """
        import gzip
        self.logger.debug("Opening mapping results file '{}' for copying to results".format(mapped_reads.mapped_reads))
        f_in = open(mapped_reads.mapped_reads, 'rb')
        self.logger.debug("Opening mapping results file destination '{}' for writing".format(target_filename))
        f_out = gzip.open(target_filename, 'wb')
        self.logger.debug("Writing compressed results to '{}' ...".format(target_filename))
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()
        self.logger.debug("Successfully created a compressed copy of the mapping results in '{}'".format(target_filename))


    def analyse(self, files, options):
        mapped_reads, temp_dir = self.preprocess_data_and_map_reads(files, options)
        if options.saveMappingResultsFile:
            target_filename = os.path.dirname(files.annotationStats)+"/"+\
                              os.path.basename(mapped_reads.mapped_reads)+".gz"
            self.save_mapping_results(mapped_reads, target_filename)
        coveragetime = time()
        self.analyse_coverage(mapped_reads, files.annotationStats, options)
        self.logger.info("Time to analyse coverage: %s", time()-coveragetime)
        self.logger.info("Results available in %s", files.annotationStats)
        if options.deleteTempFiles:
            self.delete_temporary_files(temp_dir)
        self.logger.info(" ----- ===== LOGGING COMPLETED ===== ----- ")
    
    
        
    @staticmethod
    def create_fastq_argparser():
        """
        Creates parser for FASTQ filtering and quality control options.
        """
        
        parser = argparse.ArgumentParser(add_help=False)
        quality_filtering_group = parser.add_argument_group("Quality filtering options", "Options for FASTQ")
        #TODO: Change dest to be the same as argument, e.g. fastqMinQ=>fqMinQuality. Will be useful when writing out config file with all options for future use with @saved-opts as argument.
        quality_filtering_group.add_argument("--qualityControl", dest="qualityControl",
            action="store_true", default=False,
            help="FASTQ quality control: perform quality filtering or trimming [default: %(default)s]")
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
        quality_filtering_group.add_argument("--bowtie2FilterReads", dest="bowtie2FilterReads",
            action="store_true", 
            help="bowtie2: Use bowtie2 to filter out for example human reads in the read preprocessing step [default: %(default)s].")
        quality_filtering_group.add_argument("--bowtie2FilterDB", dest="bowtie2FilterDB",
            type=str, default="", metavar="FilterDB", 
            help="bowtie2: Name of the filtering reference database tarball (including extension). It must have the same basename as the rest of the actual DB files.")
        quality_filtering_group.add_argument("--bowtie2Threads", dest="bowtie2Threads",
            type=int, default=psutil.NUM_CPUS, metavar="N", 
            help="bowtie2: Number of threads to run bowtie2 on [default %(default)s].")

        return parser
    
    
    @staticmethod
    def create_processing_argparser(argv):
        """
        Creates parser for options that describes HOW to process the files (not WHAT files are to be processed).
        
        Is used both for the single contig-file and many-contig-files cases.
        """

        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options", 
            "Select a mapper. After specifying a mapper option, combine with --help to show all available options.")

        tentacle_pkg_path = os.path.normpath(os.path.join(__file__, "..", "..")+"/mappers")
        available_mappers = [name for _, name, _, in pkgutil.iter_modules([tentacle_pkg_path])]
        available_mappers = [m for m in available_mappers if m!="mapper"]
        for mapper_name in available_mappers:
            mapping_group.add_argument("--{}".format(mapper_name), dest="mapperName", action='store_const', 
                const=mapper_name, default="", 
                help="Use '{}' for mapping".format(mapper_name))
        
        # Since the argparser for the mapping module isn't yet loaded we first need
        # to parse what mapper is requested before adding and loading all other argparsers.
        options, argv = parser.parse_known_args(argv)
        if not options.mapperName:
            parser.print_help()
            exit(0)
        #self.logger.debug("Found mapperName '{}' on command line, trying to load module '{}'.".format(options.mapperString))
        mappers = importlib.import_module(".."+options.mapperName, "tentacle.mappers.subpkg")
        mapperClass = getattr(mappers, options.mapperName.title())
        mapper = mapperClass(_, options.mapperName)
        
        parser = argparse.ArgumentParser(parents=[TentacleCore.create_fastq_argparser(), 
                                                  mapper.create_argparser()], add_help=False)
        
        debug_group = parser.add_argument_group("DEBUG developer options", "Use with caution!")
        debug_group.add_argument("--outputCoverage", dest="outputCoverage", action="store_true", default=False,
            help="Outputs complete coverage information into contigCoverage.txt")
            
        return (parser, options, argv)
        
        
    @staticmethod
    def extract_file_options(options):
        # Define original source files
        # Simple quick validity check of positional arguments.
        # No check for actual validity of content here, 
        # mappers will crash later if they are malformed.
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
    
        parser = argparse.ArgumentParser(description="Maps reads to annotations in contigs and produces corresponding stats.", 
            parents=[TentacleCore.create_processing_argparser()], add_help=True)
        
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


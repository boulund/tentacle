#!/usr/bin/env python
from os import path, listdir, mkdir
import argparse

from .. import tentacle_core
from .. import utils

# --- Public/Exported functions and classes ---

__all__ = ["TentacleMaster"]

class TentacleMaster(object):
    @staticmethod
    def parse_args(argv):
        parser = create_multiple_data_argparser()
        options = parser.parse_args()
        return options
    
    
    def process(self, options):
    #TODO: handle logging (some at creation, some for each file, possibly some for error)
        masterLogger = utils.start_logging(options.logdebug, "tentacle.log")
        utils.print_run_settings(options, masterLogger)
        log_dir, result_dir = determine_and_create_out_dirs(options)
    #TODO: print_run_settings(options)
        return identify_linked_files({"annotations":(options.annotationsDirectory, "_annotation."),
                                      "contigs":(options.contigsDirectory, "_contigs."),
                                      "reads":(options.readsDirectory, "_")},
                                      log_dir, result_dir, masterLogger)
        
# --- Private/Internal functions and classes ---
        
def core_name(file_path, end_symbol):
    filename = path.basename(file_path)
    return filename.split(end_symbol,1)[0]


def core_names_and_files(dir_path,  end_symbol):
    return map(lambda f : (core_name(f, end_symbol), path.realpath(path.join(dir_path,f))), listdir(dir_path))


def files_by_core_name(dir_path,  end_symbol):
    return dict(core_names_and_files(dir_path, end_symbol))


def identify_linked_files(dir_and_end_symbol_by_category, log_dir, result_dir, logger):
    contigs_files_by_core_name = files_by_core_name(*dir_and_end_symbol_by_category['contigs'])
    annotations_files_by_core_name = files_by_core_name(*dir_and_end_symbol_by_category['annotations'])
    reads_core_names_and_files = core_names_and_files(*dir_and_end_symbol_by_category['reads'])
    
    #identify common core names
    contigs_core_names = set(contigs_files_by_core_name.iterkeys())
    annotations_core_names = set(contigs_files_by_core_name.iterkeys()) 
    reads_core_names = set([t[0] for t in reads_core_names_and_files])
    non_complete = (reads_core_names ^ contigs_core_names) | (reads_core_names ^ annotations_core_names)
    if non_complete:
        for core_name in non_complete:
            logger.error("Incomplete file set for %s\n", core_name)
        exit(1)
    
    def create_fileset(core_name, reads_file):
        result_file = path.join(result_dir, path.basename(reads_file)+".tab")
        log_file = path.join(log_dir, path.basename(reads_file)+".log")
        return tentacle_core.AllFiles( contigs_files_by_core_name[core_name], reads_file, annotations_files_by_core_name[core_name], result_file, log_file )
                                        
    return [(core_name, create_fileset(core_name,reads_file)) for (core_name,reads_file) in reads_core_names_and_files]


def create_multiple_data_argparser():
    """
    Creates parser for all arguments for when a collection of triplets (contigs, reads, annotions) are to be processed.
    """

    parser = argparse.ArgumentParser(description="Maps reads to annotations in contigs and produces corresponding stats.", parents=[tentacle_core.TentacleCore.create_processing_argarser()], add_help=True)
    
    parser.add_argument("contigsDirectory", help="path to directory containing contigs files (gzippped FASTQ)")
    parser.add_argument("readsDirectory", help="path to directory containing read files (gzipped FASTQ)")
    parser.add_argument("annotationsDirectory", help="path to directory containing annotation files (tab separated text)")
    parser.add_argument("-o", "--outputDirectory", default="tentacle_results", dest="outputDirectory", help="path to directory being created and holding the logfiles and annotations [default =  %(default)s]")
    
    return parser


def determine_and_create_out_dirs(options):
    out_dir = options.outputDirectory
    log_dir = path.join(out_dir, "logs")
    result_dir = path.join(out_dir, "results")
    
    #TODO: Add proper handling of existing dir, now an OSError will be thrown
    mkdir(options.outputDirectory)
    mkdir(log_dir)
    mkdir(result_dir)
    return log_dir, result_dir
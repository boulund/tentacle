#!/usr/bin/env python
from os import path, listdir, mkdir
import argparse
import random
import sys

from .. import tentacle_core
from .. import utils
from output_dir_structure import OutputDirStructure

# --- Public/Exported functions and classes ---

__all__ = ["TentacleMaster"]

class TentacleMaster(object):
    @staticmethod
    def create_get_tasks_argparser():
        parser = argparse.ArgumentParser(add_help=False)
        general_group = parser.add_argument_group("General options")
        general_group.add_argument("--mappingManifest", required=True,
            help="a tab delimited text file with mapping triplets on each row")
        general_group.add_argument("--saveMappingResultsFile", action="store_true",
            help="Retrieve the mapping results file from the node after mapping completion")
        general_group.add_argument("--noCoverage", action="store_true",
            help="Skip computing coverage for all annotated regions [default: %(default)s].")
        general_group.add_argument("--noCounts", action="store_true",
            help="Skip computing counts for all annotated regions [default: %(default)s].")
        general_group.add_argument("--coverageAllAlignments", action="store_true",
            help="Include all matching alignments in coverage computations. Note that this might inflate coverage! Default is to only include the 'best' hit found in the mapper output [default %(default)s].")
        return parser
    
    @staticmethod
    def create(logger_provider):
        return TentacleMaster(logger_provider) 

    def __init__(self, logger_provider):
        self.master_logger = logger_provider.get_logger("master")
    
    def get_tasks_from_parsed_args(self, parsed_args, output_dir_structure):
        utils.print_run_settings(parsed_args, self.master_logger)
        mapping_tuples = parse_linked_files(parsed_args.mappingManifest, output_dir_structure, self.master_logger)
        return mapping_tuples



def parse_linked_files(mapping_manifest, output_dir_structure, master_logger):
    """
    Parses mapping triplets from mapping manifest file
    """
    try:
        with open(mapping_manifest) as manifest_file:
            # TODO: Test if possible to split row in 4, for paired end data
            mapping_tuples = []
            for line_number, line in enumerate(manifest_file):
                try:
                    reads, reference, annotation = line.split()
                except ValueError:
                    master_logger.error("Unable to split line {} of file {} into reads, reference, annotation".format(line_number, mapping_manifest))
                    exit(1)
                current_tuple = (reads, reference, annotation)
                for file_path in current_tuple:
                    if not path.isfile(file_path):
                        master_logger.error("The path to '{}' appears incorrect".format(file_path))
                        exit(1)
                result_file = path.join(output_dir_structure.results, path.basename(reads)+".tab")
                task_logs_dir = output_dir_structure.get_logs_subdir("task_logs")
                log_file = path.join(task_logs_dir, path.basename(reads)+"_"+str(random.randint(0,sys.maxint))+".log")
                mapping_tuples.append((core_name(reads, "."), tentacle_core.AllFiles(reference, reads, annotation, result_file, log_file)))
    except TypeError, e:
        master_logger.error("Cannot open mapping manifest file '{}'".format(mapping_manifest))
        exit(1)
            
    return mapping_tuples




# --- Private/Internal functions and classes ---
def core_name(file_path, end_symbol):
    filename = path.basename(file_path)
    return filename.split(end_symbol,1)[0]


def core_names_and_files(dir_path,  end_symbol):
    return map(lambda f : (core_name(f, end_symbol), path.join(path.realpath(dir_path), f)), listdir(dir_path))


def files_by_core_name(dir_path,  end_symbol):
    return dict(core_names_and_files(dir_path, end_symbol))


def identify_linked_files(dir_and_end_symbol_by_category, output_dir_structure, master_logger):
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
            master_logger.error("Incomplete file set for %s\n", core_name)
        exit(1)
    
    task_logs_dir = output_dir_structure.get_logs_subdir("task_logs")
    def create_fileset(core_name, reads_file):
        result_file = path.join(output_dir_structure.results, path.basename(reads_file)+".tab")
        log_file = path.join(task_logs_dir, path.basename(reads_file)+"_"+str(random.randint(0,sys.maxint))+".log")
        return tentacle_core.AllFiles( contigs_files_by_core_name[core_name], reads_file, annotations_files_by_core_name[core_name], result_file, log_file )
                                        
    return [(core_name, create_fileset(core_name,reads_file)) for (core_name,reads_file) in reads_core_names_and_files]

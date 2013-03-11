#!/usr/bin/env python
from os import path, listdir, mkdir
import argparse

from .. import tentacle_core
from .. import utils
from output_dir_structure import OutputDirStructure

# --- Public/Exported functions and classes ---

__all__ = ["TentacleMaster"]

class TentacleMaster(object):
    @staticmethod
    def create_get_tasks_argparser():
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("contigsDirectory", help="path to directory containing contigs files (gzippped FASTQ)")
        parser.add_argument("readsDirectory", help="path to directory containing read files (gzipped FASTQ)")
        parser.add_argument("annotationsDirectory", help="path to directory containing annotation files (tab separated text)")
        return parser
    
    def __init__(self, logger_provider):
        self.master_logger = logger_provider.get_logger("master")
    
    def get_tasks(self, parsed_args, output_dir_structure):
        utils.print_run_settings(parsed_args, self.master_logger)
        return identify_linked_files({"annotations":(parsed_args.annotationsDirectory, "_annotation."),
                                      "contigs":(parsed_args.contigsDirectory, "_contigs."),
                                      "reads":(parsed_args.readsDirectory, "_")},
                                      output_dir_structure, self.master_logger)
        
# --- Private/Internal functions and classes ---
def core_name(file_path, end_symbol):
    filename = path.basename(file_path)
    return filename.split(end_symbol,1)[0]


def core_names_and_files(dir_path,  end_symbol):
    return map(lambda f : (core_name(f, end_symbol), path.realpath(path.join(dir_path,f))), listdir(dir_path))


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
    
    def create_fileset(core_name, reads_file):
        result_file = path.join(output_dir_structure.results, path.basename(reads_file)+".tab")
        log_file = path.join(output_dir_structure.task_logs, path.basename(reads_file)+".log")
        return tentacle_core.AllFiles( contigs_files_by_core_name[core_name], reads_file, annotations_files_by_core_name[core_name], result_file, log_file )
                                        
    return [(core_name, create_fileset(core_name,reads_file)) for (core_name,reads_file) in reads_core_names_and_files]
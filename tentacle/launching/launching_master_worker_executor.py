import argparse
from ..output_dir_structure import OutputDirStructure

__all__ = ["LaunchingMasterWorkerExecutor"]
   
class LaunchingMasterWorkerExecutor(object):
    @classmethod
    def create_arg_parsers(Cls, Launcher, Master, Worker):
        """create parsers for the different submodules, and return along with a joint parser containing them all, along with help"""
        individual = ({"job_description" : Master.create_job_description_arg_parser(),
                       "master_init" : Master.create_init_arg_parser(),
                       "worker_init" : Worker.create_init_arg_parser(),
                       "output_dir": OutputDirStructure.create_argparser(), #TODO
                       "launch_option" : Launcher.create_launch_options_argparser(),
                       "logger_options" : None }) #TODO
        joint = argparse.ArgumentParser(description="Run the Tentacle metagenomics workflow distributed over SLURM", parents=individual.values(), add_help=True)
        return (individual, joint)
        
    @classmethod
    def parse_options(Cls, argv, Master, Worker):
        #Create the parsers
        (individual_parsers, joint_parser) = Cls.create_arg_parsers(Master, Worker)
        #Verify args and make the help section appear if asked for
        joint_parser.parse_args(argv)
        #Return one option item for each individual parser
        return ({ name:parser.parse_known_args(argv) for name,parser in individual_parsers.items() })
    
    @classmethod
    def launch_master_worker(Cls, argv, Launcher, Master, Worker):
        options_by_module = Cls.parse_options(argv, Master, Worker)
        
        outdir_structure = OutputDirStructure.new_from_parsed_args(options_by_module['output_dir'])
        outdir_structure.mkdirs()
        
        
    
        #serialize opts into output/communication/options
        #create master and worker slurm scripts, with slurm_opts
        #launch master and worker with output_dir as argument, from where they can access the communication and result dirs

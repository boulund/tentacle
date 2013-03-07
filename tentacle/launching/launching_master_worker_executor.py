import argparse
from ..output_dir_structure import OutputDirStructure

__all__ = ["LaunchingMasterWorkerExecutor"]

class LaunchingMasterWorkerExecutor(object):
    @classmethod
    def create_arg_parsers(Cls, distributed_worker_pool_factory, master_creator, worker_creator):
        """create parsers for the different submodules, and return along with a joint parser containing them all, along with help"""
        individual = ({"job_description" : master_creator.create_job_description_arg_parser(),
                       "master" : master_creator.create_arg_parser(),
                       "worker_init" : worker_creator.create_init_arg_parser(),
                       "output_dir": OutputDirStructure.create_argparser(),
                       "distributed_worker_pool" : distributed_worker_pool_factory.create_argparser(),
                       "logger_options" : None }) #TODO add logger options (Verbose)
        joint = argparse.ArgumentParser(description="Run the Tentacle metagenomics workflow distributed over SLURM", parents=individual.values(), add_help=True)
        return (individual, joint)
        
    @classmethod
    def parse_options(Cls, argv, distributor_factory, master_creator, worker_creator):
        #Create the parsers
        (individual_parsers, joint_parser) = Cls.create_arg_parsers(distributor_factory, master_creator, worker_creator)
        #Verify args and make the help section appear if asked for
        joint_parser.parse_args(argv)
        #Return one option item for each individual parser
        return ({ name:parser.parse_known_args(argv) for name,parser in individual_parsers.items() })
    
    @classmethod
    def launch_master_worker(Cls, argv, distributed_worker_pool_factory, master_factory, worker_factory, logger_provider_factory, launcher):
        options_by_module = Cls.parse_options(argv, master_factory, worker_factory)
        
        #create the dependencies
        output_dir_structure = OutputDirStructure.new_from_parsed_args(options_by_module['output_dir'])
        output_dir_structure.mkdirs() #TODO: include into the creation?
        logger_provider = logger_provider_factory.get_logger_provider(output_dir_structure.logs)
        
        #Get the tasks
        master = master_factory.create_master(logger_provider)
        tasks = master.get_tasks(options_by_module['master'], output_dir_structure)
        
        #On a separate node, create the worker pool and process the tasks
        def create_distributed_worker_pool_and_process_tasks():
            #create the distributed worker pool
            with distributed_worker_pool_factory.create_distributed_worker_pool(options_by_module['distributed_worker_pool']) as distributed_worker_pool:
                result = distributed_worker_pool.map(lambda task:worker_factory.create_worker(options_by_module['worker_init'], logger_provider).process(task), tasks)
                #TODO, what to do with results?  
        launcher.launch_python_function(create_distributed_worker_pool_and_process_tasks)
    
        #serialize opts into output/communication/options
        #create master and worker slurm scripts, with slurm_opts
        #launch master and worker with output_dir as argument, from where they can access the communication and result dirs

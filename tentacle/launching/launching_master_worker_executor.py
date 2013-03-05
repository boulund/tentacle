import argparse
from ..output_dir_structure import OutputDirStructure

__all__ = ["LaunchingMasterWorkerExecutor"]


class DistributedPool(object):
    @staticmethod
    def create():
        #setup registry service, etc
    def a
    pass
    



class LaunchingMasterWorkerExecutor(object):
    @classmethod
    def create_arg_parsers(Cls, distributor_factory, master_creator, worker_creator):
        """create parsers for the different submodules, and return along with a joint parser containing them all, along with help"""
        individual = ({"job_description" : master_creator.create_job_description_arg_parser(),
                       "master" : master_creator.create_arg_parser(),
                       "worker_init" : worker_creator.create_init_arg_parser(),
                       "output_dir": OutputDirStructure.create_argparser(),
                       "distributor" : distributor_factory.create_argparser(),
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
    def launch_master_worker(Cls, argv, distributor_factory, master_factory, worker_factory, logger_provider_factory):
        options_by_module = Cls.parse_options(argv, master_factory, worker_factory)
        
        #create the dependencies
        output_dir_structure = OutputDirStructure.new_from_parsed_args(options_by_module['output_dir'])
        output_dir_structure.mkdirs() #TODO: include into the creation?
        logger_provider = logger_provider_factory.get_logger_provider(output_dir_structure.logs)
        distributor = distributor_factory.create_distributor(options_by_module['distributor'])
        
        #Get the tasks
        def create_master_and_get_tasks():
            master = master_factory.create_master(logger_provider)
            return master.process(options_by_module['master'], output_dir_structure)
        tasks = create_master_and_get_tasks()
        
        #Define the operations to be performed on the worker nodes
        def worker_node_operation_producer():
            worker = worker_factory.create_worker(options_by_module['worker_init'], logger_provider)
            op = (lambda task: worker.process(task))
            return op
        
        #Launch the parallel work using a parallel for
        async_for_handle = distributor.async_for(tasks = tasks, operation_producer = worker_node_operation_producer)
        
        return async_for_handle
        
        
        def run_a_distributed_master():
            team = distributed_worker_team_provider.create_team_for_processing(output_dir_structure.communication, logger_provider)
            results = team.process(tasks)
            #TODO: what to do with results, write back?
        
        def run_a_distributed_worker():
            worker = worker_factory.create_worker(options_by_module['worker_init'], logger_provider)
            team = distributed_worker_team_provider.find_team_for_joining(output_dir_structure.communication)
            team.join_and_work(worker)
        
        worker_count = 50 #TODO: Get this from opts
        capped_worker_count = min(len(tasks),worker_count)
        spawned_master = distributor.spawn(run_a_distributed_master)
        spawned_workers = [distributor.spawn(run_a_distributed_worker) for _ in range(capped_worker_count)]
        return (spawned_master, spawned_workers)  
            
            
    
        #serialize opts into output/communication/options
        #create master and worker slurm scripts, with slurm_opts
        #launch master and worker with output_dir as argument, from where they can access the communication and result dirs

import argparse
from output_dir_structure import OutputDirStructure
from tentacle.launching.launchers import SubprocessLauncher
from ..utils.logging_utils import LoggerProvider
from tentacle.launching.zero_rpc_worker_pool import ZeroRpcDistributedWorkerPoolFactory

__all__ = ["LaunchingMasterWorkerExecutor"]

class LaunchingMasterWorkerExecutor(object):
    @classmethod
    def parse_options(Cls, argv, master_factory, worker_factory, launcher_factory, distributed_worker_pool_factory, logger_provider_factory, output_dir_structure_factory):
        """create parsers for the different submodules, and return along with a joint parser containing them all, along with help"""
        parsers = [master_factory.create_get_tasks_argparser(),
                   worker_factory.create_argparser(),
                   output_dir_structure_factory.create_argparser(),
                   distributed_worker_pool_factory.create_argparser(),
                   launcher_factory.create_argparser(),
                   logger_provider_factory.create_argparser()]
        
        joint_parser = argparse.ArgumentParser(description="Run the distributed Tentacle metagenomics workflow", parents=parsers, add_help=True)
        
        #Parse the args and make the help section appear if asked for
        return joint_parser.parse_args(argv[1:])
    
    @classmethod
    def launch_master_worker(Cls, argv, master_factory, worker_factory, launcher_factory=SubprocessLauncher, distributed_worker_pool_factory=ZeroRpcDistributedWorkerPoolFactory(), logger_provider_factory=LoggerProvider, output_dir_structure_factory = OutputDirStructure):
        parsed_args = Cls.parse_options(argv, master_factory, worker_factory, launcher_factory, distributed_worker_pool_factory, logger_provider_factory, output_dir_structure_factory)
        
        #create the dependencies
        output_dir_structure = output_dir_structure_factory.create_from_parsed_args(parsed_args)
        stdio_dir_path = output_dir_structure.get_logs_subdir("stdio")
        logger_provider = logger_provider_factory.create_from_parsed_args(parsed_args, output_dir_structure.logs)
        launcher = launcher_factory.create_from_parsed_args(stdio_dir=stdio_dir_path, parsed_args=parsed_args)
        
        #Get the tasks
        master = master_factory.create(logger_provider)
        tasks = master.get_tasks_from_parsed_args(parsed_args, output_dir_structure)
        
        #In a remote process, create the worker pool and get_tasks the tasks
        def create_distributed_worker_pool_and_process_tasks():
            #create the distributed worker pool
            #TODO: handle logging/exceptions
            with distributed_worker_pool_factory.create_from_parsed_args(parsed_args, launcher) as distributed_worker_pool:
                distributed_worker_pool.map(
                    lambda task: worker_factory.create_from_parsed_args(parsed_args, logger_provider).process(task), #pylint: disable=W0108
                    tasks)
                #TODO, what to do with results?  
        return launcher.launch_python_function(create_distributed_worker_pool_and_process_tasks)


#Main TODO: Create driving test, running the app for test data (using localLauncher)
#- examine files, etc, check absolute paths
#- run it on Slurm.

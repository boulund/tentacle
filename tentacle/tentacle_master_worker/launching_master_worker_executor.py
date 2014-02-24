import argparse
from output_dir_structure import OutputDirStructure
from tentacle.launching.launchers import SubprocessLauncher
from ..utils.logging_utils import LoggerProvider
from tentacle.launching.zero_rpc_worker_pool import ZeroRpcDistributedWorkerPoolFactory
import gevent

__all__ = ["LaunchingMasterWorkerExecutor"]

class LaunchingMasterWorkerExecutor(object):
    @classmethod
    def create_argparser(cls):
        parser = argparse.ArgumentParser(add_help=False)
        group = parser.add_argument_group("Launching options")
        group.add_argument("--localCoordinator", action="store_true",
            default=False,
            help="Run the processing coordinator locally, synchronously in the current process,\
                  instead of launching it in a remote process. [default =  %(default)s]")
        group.add_argument("--splitCharReads", type=str, default=".", metavar="C",
            help="Character used to split filenames of reads [default=%(default)s]")
        group.add_argument("--splitCharAnnotations", type=str, default=".", metavar="C",
            help="Character used to split filenames of annotations [default=%(default)s]")
        group.add_argument("--splitCharReferences", type=str, default=".", metavar="C",
            help="Character used to split filenames of references [default=%(default)s]")
        parser.add_argument_group(group)
        return parser     
    
    @classmethod
    def parse_options(cls, 
                      argv, 
                      master_factory, 
                      worker_factory, 
                      launcher_factory, 
                      distributed_worker_pool_factory, 
                      logger_provider_factory, 
                      output_dir_structure_factory):
        """create parsers for the different submodules, and return along 
        with a joint parser containing them all, along with help"""

        worker_argparser, mapper_namespace, argv = worker_factory.create_argparser(argv)

        parsers = [cls.create_argparser(),
                   master_factory.create_get_tasks_argparser(),
                   worker_argparser,  
                   output_dir_structure_factory.create_argparser(),
                   distributed_worker_pool_factory.create_argparser(),
                   launcher_factory.create_argparser(),
                   logger_provider_factory.create_argparser()]
        
        joint_parser = argparse.ArgumentParser(description="Run the distributed Tentacle metagenomics workflow",
            parents=parsers, add_help=True)
        
        #Parse the remaining args and make the help section appear if asked for
        return joint_parser.parse_args(argv[1:], namespace=mapper_namespace)
    
    @classmethod
    def launch_master_worker(cls, argv, 
                             master_factory, 
                             worker_factory, 
                             launcher_factory=SubprocessLauncher, 
                             distributed_worker_pool_factory=ZeroRpcDistributedWorkerPoolFactory(), 
                             logger_provider_factory=LoggerProvider, 
                             output_dir_structure_factory=OutputDirStructure):

        parsed_args = cls.parse_options(argv, 
                                        master_factory, 
                                        worker_factory, 
                                        launcher_factory, 
                                        distributed_worker_pool_factory, 
                                        logger_provider_factory,
                                        output_dir_structure_factory)
        
        #create the dependencies
        output_dir_structure = output_dir_structure_factory.create_from_parsed_args(parsed_args)
        print("Output dir: " + output_dir_structure.output)
        stdio_dir_path = output_dir_structure.get_logs_subdir("stdio")
        logger = logger_provider_factory.create_from_parsed_args(parsed_args, output_dir_structure.logs)
        launcher = launcher_factory.create_from_parsed_args(stdio_dir=stdio_dir_path, parsed_args=parsed_args)
        
        #Get the tasks
        master = master_factory.create(logger)
        tasks = master.get_tasks_from_parsed_args(parsed_args, output_dir_structure)
        return cls.launch_worker_pool_and_process_tasks(parsed_args, worker_factory, distributed_worker_pool_factory, logger, launcher, tasks)

    @classmethod
    def launch_worker_pool_and_process_tasks(cls, parsed_args, worker_factory, distributed_worker_pool_factory, logger_provider, launcher, tasks):
        def create_distributed_worker_pool_and_process_tasks():
            """Creating the worker pool (with launched workers) and processing the tasks"""
            #create the distributed worker pool
            #TODO: handle logging/exceptions
            with distributed_worker_pool_factory.create_from_parsed_args(parsed_args, launcher) as distributed_worker_pool:
                distributed_worker_pool.map(
                    lambda task: worker_factory.create_from_parsed_args(parsed_args, logger_provider).process(task), tasks)
                #TODO, what to do with results?

        if parsed_args.localCoordinator:
            return gevent.spawn(create_distributed_worker_pool_and_process_tasks)
        else:
            return launcher.launch_python_function(create_distributed_worker_pool_and_process_tasks)

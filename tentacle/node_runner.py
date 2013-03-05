import collections
import tentacle_master_worker


Options = collections.namedtuple("Options", ["zerorpc_master_worker_executor", "tentacle_master", "tentacle_worker"])

def run(role, shell_setup_code, options_file_path):
    from zerorpc_master_worker_executor import Executor
    from tentacle_master_worker import TentacleMaster, TentacleMaster
    
    options = deserialize_options(options_file_path)
    
    e_options = options.zerorpc_master_worker_executor
    mw_executor = call(Executor, e_options)
    
    if role=="master":
        master = tentacle_master_worker.TentacleMaster()
        call(master.process, options.tentacle_master)
    elif role =="worker":
        worker = tentacle_master_worker.TentacleWorker(options)
        worker.
        call(master.process, options.tentacle_master)
        
    mw_options = options.tentacle_master_worker
    master_worker = call(MasterWorker, mw_options)
    
    mw_executor.DoWork(master_worker, role)

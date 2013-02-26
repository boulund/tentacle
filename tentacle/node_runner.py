import collections

def call(o, arguments):
    o.__call__(*arguments.get('args',list()), **arguments.get('kwargs',dict()))

def serialize_options(options, options_file_path):
    import pickle
    with open(options_file_path, 'w') as f:
        pickle.dump(options, f)

def deserialize_options(options_file_path):
    import pickle
    with open(options_file_path, 'r') as f:
        return pickle.load(f)

Options = collections.namedtuple("Options", ["zerorpc_master_worker_executor", "tentacle_master_worker"])

def run(role, shell_setup_code, options_file_path):
    from zerorpc_master_worker_executor import Executor
    from tentacle_master_worker import MasterWorker
    
    options = deserialize_options(options_file_path)
    
    e_options = options.zerorpc_master_worker_executor
    mw_executor = call(Executor, e_options)
    
    mw_options = options.tentacle_master_worker
    master_worker = call(MasterWorker, mw_options)
    
    mw_executor.HelpProcess(master_worker, role)

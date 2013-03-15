from __future__ import print_function
import argparse
import gevent
import zerorpc
from ..utils import ScopedObject
from ..utils.zerorpc_utils import run_single_rpc, spawn_server
from ..serialization.cloud_serializer import CloudSerializer
from .registering_worker_pool import Worker, RegisteringWorkerPool
from .launchers import GeventLauncher, SubprocessLauncher

def _debugPrint(msg): 
    pass
    print(msg) #comment out in production code

__all__ = []

__all__.append("ZeroRpcWorkerPool")
class ZeroRpcWorkerPool(RegisteringWorkerPool):
    def __init__(self):
        super(ZeroRpcWorkerPool, self).__init__()
        self._endpoints = None #Is needed since zerorpc invokes endpoints property for some reason when starting server
        s, self._endpoints = spawn_server(self)
        _debugPrint("Started ZeroRpcWorkerPool server with endpoints: " + " ".join(self._endpoints))
        self._scope.on_exit(lambda: _debugPrint("Stopping ZeroRpcWorkerPool server"),
                            lambda: s.stop())
    @property
    def endpoints(self): 
        return self._endpoints
    
    def register_remote_worker(self, worker_endpoints):
        _debugPrint("ZeroRpcWorkerPool registering worker with endpoints: " + " ".join(worker_endpoints))
        worker = self.WorkerProxy(worker_endpoints)
        self.register_worker(worker)
                
    class WorkerProxy(ScopedObject):
        def __init__(self, worker_endpoints):
            self._worker_endpoints = worker_endpoints
            _debugPrint("Creating worker proxy for " + " ".join(worker_endpoints))
            super(ZeroRpcWorkerPool.WorkerProxy, self).__init__()

            _debugPrint("Creating zerorpc.Client")
            self._zerorpc_client = zerorpc.Client(timeout=10000) #TODO: add back
            self._scope.on_exit(lambda: _debugPrint("Closing zerorpc.Client for " + " ".join(worker_endpoints)),
                                self._zerorpc_client.close)
            
            _debugPrint("Connecting zerorpc.Client to " + " ".join(worker_endpoints))
            self._zerorpc_client.connect(worker_endpoints[0])
            self._scope.on_exit(lambda: _debugPrint("Send close call to worker at " + " ".join(worker_endpoints)),
                                lambda: self._zerorpc_client("close")) #Send a close call to the worker side, note that this will be done _before_ self.zerorpc_client.close above

        def run(self, task):
            _debugPrint("running task at "  + " ".join(self._worker_endpoints))
            return self._zerorpc_client.run_serialized(CloudSerializer().serialize_to_string(task))


__all__.append("ZeroRpcWorkerPoolWorker")
class ZeroRpcWorkerPoolWorker(Worker):
    def __init__(self):
        super(ZeroRpcWorkerPoolWorker, self).__init__()
        self._endpoints = None #Is needed since zerorpc invokes endpoints property for some reason when starting server
        s, self._endpoints = spawn_server(self)
        _debugPrint("Started ZeroRpcWorkerPoolWorker server with endpoints: " + " ".join(self._endpoints))
        self._scope.on_exit(lambda: _debugPrint("Stopping ZeroRpcWorkerPoolWorker server " + " ".join(self._endpoints)),
                            s.stop)
    @property
    def endpoints(self): 
        return self._endpoints
    
    def run_serialized(self, serialized_task):
        _debugPrint("ZeroRpcWorkerPoolWorker: run_serialized called")
        task = CloudSerializer().deserialize_from_string(serialized_task)
        return self.run(task)
    
    @staticmethod
    def create_worker_runner(pool_endpoints, timeout=None):
        def run_remote_worker():
            w = ZeroRpcWorkerPoolWorker()
            register_zero_rpc_pool_worker_at_remote_pool(w, pool_endpoints)
            w.closed.wait(timeout)
            if not w.closed.is_set():
                w.close() #needed if timed out     
        return run_remote_worker


def register_zero_rpc_pool_worker_at_remote_pool( worker, zero_rpc_worker_pool_endpoints ):
    run_single_rpc(zero_rpc_worker_pool_endpoints,
                   lambda registry: registry.register_remote_worker(worker.endpoints))


__all__.append("ZeroRpcDistributedWorkerPoolFactory")
class ZeroRpcDistributedWorkerPoolFactory(object):
    def create_argparser(self):
        parser = argparse.ArgumentParser(add_help=False)
        group = parser.add_argument_group("General distribution options")
        group.add_argument("-N", "--distributionNodeCount", dest="node_count", type=int,
            default=1,
            help="The number of distributed nodes to run on. [default =  %(default)s]")
        group.add_argument("--distributionUseDedicatedCoordinatorNode", dest="use_dedicated_coordinator",
            action="store_true", default=False,
            help="Should a dedicated coordinator node be launched (instead of also processing jobs on that node). [default =  %(default)s]")
        parser.add_argument_group(group)
        return parser
    
        
    def create_from_parsed_args(self, parsed_args, remote_launcher, local_launcher=GeventLauncher()):
        return self.create(worker_count=parsed_args.node_count, 
                           use_dedicated_coordinator=parsed_args.use_dedicated_coordinator, 
                           remote_launcher=remote_launcher, local_launcher=local_launcher)
    
    
    def create(self, remote_launcher, worker_count, use_dedicated_coordinator, local_launcher=GeventLauncher()):
        #Create the pool
        pool = ZeroRpcWorkerPool()
        try:
            #Launch the workers
            if worker_count==0:
                return
            worker_runner = ZeroRpcWorkerPoolWorker.create_worker_runner(pool.endpoints)
            
            if use_dedicated_coordinator:
                remote_worker_count = worker_count
            else:
                local_launcher.launch_python_function(worker_runner)
                remote_worker_count = worker_count - 1
            
            for _ in range(remote_worker_count):
                remote_launcher.launch_python_function(worker_runner)
        except:
            pool.close()
            raise
        return pool
            

import unittest
import itertools

def _create_stdio_dir():
    import tempfile
    d = tempfile.mkdtemp()
    print("stdio-dir: " + d)
    return d
    
def _test_map(pool, test_case):
    def identity(i):
        if i==0: gevent.sleep(0) #yield before returning the results. Checking that the order of the results is correct anyways.
        return i
    inseq = range(10)
    res = pool.map(identity,inseq)
    test_case.assertSequenceEqual([r.get() for r in res], inseq)
    
class ZeroRpcWorkerPoolTests(unittest.TestCase):
    def Test_map(self):
        pool = ZeroRpcWorkerPool()
        with pool:
            ws = [ZeroRpcWorkerPoolWorker() for _ in range(3)]
            for w in ws: 
                register_zero_rpc_pool_worker_at_remote_pool(w, pool.endpoints)
            _test_map(pool, self)
        self.assert_(pool.closed.is_set())
        for w in ws: 
            self.assert_(w.closed.is_set())

    def Test_a_serialize_run_remote_worker(self):
        runner = ZeroRpcWorkerPoolWorker.create_worker_runner("tcp://127.0.0.1:1234", 10)
        s=CloudSerializer().serialize_to_string(runner)
        CloudSerializer().deserialize_from_string(s)

    def Test_map_different_process(self):
        timeout = 10
        pool = ZeroRpcWorkerPool()
        with pool:        
            SubprocessLauncher(stdio_dir=_create_stdio_dir()).launch_python_function(ZeroRpcWorkerPoolWorker.create_worker_runner(pool.endpoints, timeout))                
            _test_map(pool, self)
        self.assert_(pool.closed.is_set())


class ZeroRpcDistributedWorkerPoolFactoryTests(unittest.TestCase):
    def Test_map_different_process(self):
        print()
        for (worker_count, do_launch_local_worker) in itertools.product([1,2,10],[True,False]):
            print()
            print("Testing with (worker_count, do_launch_local_worker) = " + str((worker_count, do_launch_local_worker)))
            pool = ZeroRpcDistributedWorkerPoolFactory().create(SubprocessLauncher(stdio_dir=_create_stdio_dir()), worker_count=worker_count, use_dedicated_coordinator=True, local_launcher=GeventLauncher())
            with pool:        
                _test_map(pool, self)
            self.assert_(pool.closed.is_set())
        
        
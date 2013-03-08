from __future__ import print_function
import unittest
import gevent
import zerorpc
from ..utils import ScopedObject
from ..zerorpc_utils import run_single_rpc, spawn_server
from ..serialization.cloud_serializer import CloudSerializer
from .registering_worker_pool import Worker, RegisteringWorkerPool
from .launchers import *

def _debugPrint(msg): 
    pass
    print(msg) #comment out in production code


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
            self._zerorpc_client = zerorpc.Client();
            self._scope.on_exit(lambda: _debugPrint("Closing zerorpc.Client for " + " ".join(worker_endpoints)),
                                self._zerorpc_client.close)
            
            _debugPrint("Connecting zerorpc.Client to " + " ".join(worker_endpoints))
            self._zerorpc_client.connect(worker_endpoints[0])
            self._scope.on_exit(lambda: _debugPrint("Send close call to worker at " + " ".join(worker_endpoints)),
                                lambda: self._zerorpc_client("close")) #Send a close call to the worker side, note that this will be done _before_ self.zerorpc_client.close above

        def run(self, task):
            _debugPrint("running task at "  + " ".join(self._worker_endpoints))
            return self._zerorpc_client.run_serialized(CloudSerializer().serialize_to_string(task))


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
    def create_runner(pool_endpoints, timeout=None):
        def run_remote_worker():
            w = ZeroRpcWorkerPoolWorker()
            register_zero_rpc_pool_worker_at_remote_pool(w, pool_endpoints)
            w.closed.wait(timeout)
            gevent.sleep() #workaround: yield to wait for the close call to have ended
            w.close() #needed if timed out, ok to close twice if not        
        return run_remote_worker


def register_zero_rpc_pool_worker_at_remote_pool( worker, zero_rpc_worker_pool_endpoints ):
    run_single_rpc(zero_rpc_worker_pool_endpoints,
                   lambda registry: registry.register_remote_worker(worker.endpoints))


class ZeroRpcWorkerPoolTests(unittest.TestCase):
    def Test_map(self):
        pool = ZeroRpcWorkerPool()
        with pool:
            def identity(i):
                if i==0: gevent.sleep(0) #yield before returning the results. Checking that the order of the results is correct anyways.
                return i
            ws = [ZeroRpcWorkerPoolWorker() for _ in range(3)]
            for w in ws: 
                register_zero_rpc_pool_worker_at_remote_pool(w, pool.endpoints)
            inseq = range(10)
            res = pool.map(identity,inseq)
            self.assertSequenceEqual([r.get() for r in res], inseq)
        self.assert_(pool.closed.is_set())
        for w in ws: 
            self.assert_(w.closed.is_set())

    def Test_a_serialize_run_remote_worker(self):
        runner = ZeroRpcWorkerPoolWorker.create_runner("tcp://127.0.0.1:1234", 10)
        s=CloudSerializer().serialize_to_string(runner)
        CloudSerializer().deserialize_from_string(s)

    def Test_map_different_process(self):
        timeout = 10
        pool = ZeroRpcWorkerPool()
        with pool:
            def identity(i):
                if i==0: gevent.sleep(0) #yield before returning the results. Checking that the order of the results is correct anyways.
                return i
                
            for _ in range(1):
                LocalLauncher().launch_python_function(ZeroRpcWorkerPoolWorker.create_runner(pool.endpoints, timeout))
                
            inseq = range(10)
            res = pool.map(identity,inseq)
            
            self.assertSequenceEqual([r.get() for r in res], inseq)
        self.assert_(pool.closed.is_set())


    
        
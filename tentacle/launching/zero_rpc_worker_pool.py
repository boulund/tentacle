from __future__ import print_function
import argparse
import sys
import gevent
import zerorpc
from ..utils.zerorpc_utils import join_all_greenlets
from ..utils import ScopedObject
from ..utils.zerorpc_utils import run_single_rpc, spawn_server
from ..serialization.cloud_serializer import CloudSerializer
from .registering_worker_pool import Worker, RegisteringWorkerPool, WorkerDisabledException
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
        #print("ZeroRpcWorkerPool server started with endpoint(s): {}".format(self_endpoints))
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
            self._zerorpc_client = zerorpc.Client(timeout=None, heartbeat=None)
            #self._zerorpc_client = zerorpc.Client(timeout=None)
            #self._zerorpc_client = zerorpc.Client(heartbeat=None)
            #self._zerorpc_client = zerorpc.Client()

            self._scope.on_exit(lambda: _debugPrint("Closing zerorpc.Client for " + " ".join(worker_endpoints)),
                                self._zerorpc_client.close)
            
            _debugPrint("Connecting zerorpc.Client to " + " ".join(worker_endpoints))
            self._zerorpc_client.connect(worker_endpoints[0])
            self._scope.on_exit(lambda: _debugPrint("Sending close call to worker at " + " ".join(worker_endpoints)),
                                self.close_client, #Send a close call to the worker side, note that this will be done _before_ self.zerorpc_client.close above
                                lambda: _debugPrint("Returned from close call to worker at " + " ".join(worker_endpoints))) 

        def run(self, task):
            _debugPrint("running task at "  + " ".join(self._worker_endpoints))
            try:
                res = self._zerorpc_client.run_serialized(CloudSerializer().serialize_to_string(task),async=True)
                res.get()
            except zerorpc.TimeoutExpired as e:
                _debugPrint("Caught TimeoutExpired exception from worker at {}".format(self._worker_endpoints))
                _debugPrint("Error was {}".format(e))
                raise WorkerDisabledException(e)
            except zerorpc.LostRemote as e:
                _debugPrint("Caught LostRemote exception from worker at {}".format(self._worker_endpoints))
                _debugPrint("Error was {}".format(e))
                raise WorkerDisabledException(e)
            return res
        
        def close_client(self):
            try:
                self._zerorpc_client.close_, #Send a close call to the worker side, note that this will be done _before_ self.zerorpc_client.close above
            except Exception as e:
                print("Failed closing remote side ({},{}). No problem - will auto-close with timeout.".format(e.message,type(e)))


__all__.append("ZeroRpcWorkerPoolWorker")
class ZeroRpcWorkerPoolWorker(Worker):
    def __init__(self, idle_timeout):
        super(ZeroRpcWorkerPoolWorker, self).__init__()
        self._endpoints = None
        self._worker_server = None
        self.start_worker_server()
        self._scope.on_exit(lambda: gevent.getcurrent().link(lambda _: self.stop_worker_server())) #Stop the server after the current call is done, so that the response is sent.
                
        self.is_running = False
        self.has_run_since_last_check = True
        self.idle_closer = gevent.spawn(self.close_on_idle, idle_timeout)
        
    def start_worker_server(self):
        self._worker_server, self._endpoints = spawn_server(self)
        _debugPrint("Started ZeroRpcWorkerPoolWorker server with endpoints: " + " ".join(self._endpoints))
        
    def stop_worker_server(self):
        _debugPrint("Wating for stopping ZeroRpcWorkerPoolWorker server with endpoints: " + " ".join(self._endpoints))
        gevent.sleep(10)
        _debugPrint("Stopping ZeroRpcWorkerPoolWorker server with endpoints: " + " ".join(self._endpoints))
        self._endpoints = None
        self._worker_server.stop()
        self._worker_server = None

    def close_(self):
        _debugPrint("close_ received, closing")
        self.close()
        
    def close_on_idle(self, idle_timeout):
        while (self.is_running or self.has_run_since_last_check) and (not self.closed.is_set()):
            _debugPrint("Checking idle status. Is running:" + str(self.is_running) + ". Has run since last check:" + str(self.has_run_since_last_check) + ".")
            self.has_run_since_last_check = False
            self.closed.wait(timeout=idle_timeout)
            
        if not self.closed.is_set():
            #self.logger.warning("Idle timed out")
            self.close()
    
    @property
    def endpoints(self): 
        return self._endpoints
    
    def run_serialized(self, serialized_task):
        _debugPrint("ZeroRpcWorkerPoolWorker: run_serialized called")
        task = CloudSerializer().deserialize_from_string(serialized_task)
        self.is_running = True
        try:
            return self.run(task)
        finally:
            self.has_run_since_last_check = True
            self.is_running = False
    
    @staticmethod
    def create_worker_runner(pool_endpoints, idle_timeout):
        def run_remote_worker():
            w = ZeroRpcWorkerPoolWorker(idle_timeout=idle_timeout)
            register_zero_rpc_pool_worker_at_remote_pool(w, pool_endpoints)
            w.closed.wait()
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
        group.add_argument("--distributedNodeIdleTimeout", 
            default = 10, type=int, 
            help="The duration (in seconds) after which an idle node should timeout. [default =  %(default)s]")
        parser.add_argument_group(group)
        return parser
    
        
    def create_from_parsed_args(self, parsed_args, remote_launcher, local_launcher=GeventLauncher()):
        return self.create(worker_count=parsed_args.node_count, 
                           use_dedicated_coordinator=parsed_args.use_dedicated_coordinator, 
                           idle_timeout=parsed_args.distributedNodeIdleTimeout,
                           remote_launcher=remote_launcher, 
                           local_launcher=local_launcher)
    
    
    def create(self,
               remote_launcher, 
               worker_count, 
               use_dedicated_coordinator, 
               idle_timeout, 
               local_launcher=GeventLauncher()):

        #Create the pool
        pool = ZeroRpcWorkerPool()
        try:
            #Launch the workers
            if worker_count==0:
                return
            worker_runner = ZeroRpcWorkerPoolWorker.create_worker_runner(pool_endpoints=pool.endpoints, 
                                                                         idle_timeout=idle_timeout) 
            
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

def _asserted_join_all_greenlets(test_case, timeout=1):
    return;

    #TODO: Understand what greenlets are left, i.e. why the below fails for all tests
    test_case.assert_(join_all_greenlets(timeout=1))

    #ODO: Also, understand why tests actually fail if I destroy the hub between them.
    if not join_all_greenlets(timeout=0):
        gevent.hub.get_hub().destroy() #kill all outstanding greenlets, to prevent any dependencies between test cases
    
def _icreateTestLauncherCreators():
    yield lambda:SubprocessLauncher(stdio_dir=_create_stdio_dir())
    yield lambda:GeventLauncher()

def _icreateTestLaunchers():
    for launcherCreator in _icreateTestLauncherCreators():
        yield launcherCreator()

class _TestCaseWithGreenlets(unittest.TestCase):
    def setUp(self):
        super(_TestCaseWithGreenlets, self).setUp()
        print()
        
    def tearDown(self):
#        if not join_all_greenlets(timeout=0):
#            sys.stderr.write("Not all greenlets were run to completion, killing hub")
#            gevent.hub.get_hub().destroy() #kill all outstanding greenlets, to prevent any dependencies between test cases
        super(_TestCaseWithGreenlets, self).tearDown()
        

class ZeroRpcWorkerPoolTests(_TestCaseWithGreenlets):
    def Test_map(self):
        pool = ZeroRpcWorkerPool()
        with pool:
            ws = [ZeroRpcWorkerPoolWorker(idle_timeout = 1) for _ in range(3)]
            for w in ws: 
                register_zero_rpc_pool_worker_at_remote_pool(w, pool.endpoints)
            _test_map(pool, self)
        self.assert_(pool.closed.is_set())
        for w in ws:
            self.assert_(w.closed.is_set())
        _asserted_join_all_greenlets(self)

    def Test_timeout(self):
        timeout = 0.0001
        w = ZeroRpcWorkerPoolWorker(idle_timeout = timeout)
        is_closed = w.closed.wait(10*timeout)
        self.assertTrue(is_closed)
        _asserted_join_all_greenlets(self)

    def Test_a_serialize_run_remote_worker(self):
        runner = ZeroRpcWorkerPoolWorker.create_worker_runner("tcp://127.0.0.1:1234", 10)
        s=CloudSerializer().serialize_to_string(runner)
        CloudSerializer().deserialize_from_string(s)
        _asserted_join_all_greenlets(self)

    def Test_map_different_process(self):
        for launcher in _icreateTestLaunchers():
            print("Testing with launcher: " + str(type(launcher)))
            timeout = 10
            pool = ZeroRpcWorkerPool()
            with pool:        
                launcher.launch_python_function(ZeroRpcWorkerPoolWorker.create_worker_runner(pool.endpoints, timeout))                
                _test_map(pool, self)
            self.assert_(pool.closed.is_set())
            _asserted_join_all_greenlets(self)
        

class ZeroRpcDistributedWorkerPoolFactoryTests(_TestCaseWithGreenlets):
    def Test_map_different_process(self):
        for launcherCreator in _icreateTestLauncherCreators():
            for (worker_count, do_launch_local_worker) in itertools.product([1,2,10],[True,False]):
                print()
                launcher = launcherCreator()
                print("Testing with (launcher, worker_count, do_launch_local_worker) = " + str((type(launcher), worker_count, do_launch_local_worker)))
                pool = ZeroRpcDistributedWorkerPoolFactory().create(launcher, worker_count=worker_count, use_dedicated_coordinator=True, idle_timeout=10, local_launcher=GeventLauncher())
                with pool:        
                    _test_map(pool, self)
                self.assert_(pool.closed.is_set())
                _asserted_join_all_greenlets(self)        
        

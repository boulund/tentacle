from __future__ import print_function
import traceback
import unittest
import gevent
import gevent.monkey
import zerorpc
from ..gevent_utils import IterableQueue
from ..utils import ScopedObject
from ..zerorpc_utils import run_single_rpc, spawn_server

gevent.monkey.patch_subprocess()


class Worker(ScopedObject):
    def run(self, task):
        result = apply(task,[])
        return result


class ZeroRpcWorkerProxy(ScopedObject, zerorpc.Client):
    def __init__(self):
        super(ZeroRpcWorkerProxy, self).__init__()
        #On close: Close the connection
        self._scope.on_exit(lambda:zerorpc.Client.close(self))
        #On close: Send a close call to the worker side. 
        #Note that on_exit methods are run in reverse order, so this happens before closing the connection above.
        self._scope.on_exit(self("close"))
    #TODO: insert worker.closed.link(server.close) into code calling this
    def close(self):
        ScopedObject.close(self)
        # zerorpc.Client.close is called by a ScopedObject exit handler, as registered in __init__


class ZeroRpcWorkerRegistry(object):
    """A worker registry facade where the endpoint of ZeroRpc-workers are registered instead of plain worker objects"""
    def __init__(self, worker_registry):
        self.worker_registry = worker_registry
        
    def register_worker(self, worker_endpoint):
        worker = ZeroRpcWorkerProxy(worker_endpoint)
        self.worker_registry.register_worker(worker)
        #TODO: Make sure worker is closed as part of closing down the registry.
    
        
class RegisteringWorkerPool(ScopedObject):
    def __init__(self):
        #TODO: Handle errors in init?
        super(RegisteringWorkerPool, self).__init__()
        self.tasks_with_result_slots_queue = IterableQueue()
        self.working_greenlets = IterableQueue()
        self._scope.on_exit(lambda: self.working_greenlets.close(), #close for adding more entries
                            lambda: self.tasks_with_result_slots_queue.close(), #close for adding more entries
                            lambda: [g.join() for g in self.working_greenlets])

    def register_worker(self, worker):
        #Start a greenlet that puts the worker to work, processing tasks from the queue
        g = gevent.Greenlet(self._process_tasks_from_queue, worker)
        self.working_greenlets.put(g)
        g.start()
        
    def _process_tasks_from_queue(self, worker):
        with worker:
            for (task,async_result) in self.tasks_with_result_slots_queue:
                print("processing an item")
                try:
                    result = task() #worker.run(task) #TODO:Add back
                    async_result.set(result)
                except Exception as e:
                    #self.logger.error("Error when trying to execute task {} by worker {}\n{}".format(task, worker, traceback.format_exc()))
                    async_result.set_exception(e)
                #print "Done   " + workerEndpoint + " to process " + str(task)
    
    class UnaryFunctionCall(object):
        def __init__(self, f, a):
            self.f = f
            self.a = a
        def __call__(self):
            result = self.f(self.a)
            return result        
            
    def map(self, f, items):
        tasks_and_results = [(self.UnaryFunctionCall(f,item), gevent.event.AsyncResult()) for item in items]
        self.tasks_with_result_slots_queue.put_many(tasks_and_results)
        for (item,async_result) in tasks_and_results:
            async_result.wait()
        results = [r for (_,r) in tasks_and_results]
        return results


class ZeroRpcWorkerPool(RegisteringWorkerPool):
    def __init__(self):
        super(ZeroRpcWorkerPool, self).__init__()
        s, self._endpoints = spawn_server(ZeroRpcWorkerRegistry(self))
        self._on_exit(lambda: print("Stopping ZeroRpcWorkerRegistry server"),
                      lambda: s.stop())
    @property
    def worker_registry_endpoints(self): 
        return self._endpoints


class ZeroRpcWorkerPoolWorker(Worker):
    def __init__(self, zero_rpc_worker_pool_registry_endpoints):
        super(ZeroRpcWorkerPoolWorker, self).__init__()
        s, local_worker_endpoints = spawn_server(self)
        self._on_exit(s.stop)
        run_single_rpc(local_worker_endpoints,
                       lambda registry: registry.register_worker(local_worker_endpoints[0])) #todo: handle possible many endpoints better
        #Handle failure, by setting self to done, and stopping server

class RegisteringWorkerPoolTests(unittest.TestCase):
    @staticmethod
    def _create_pool():
        from ..utils.logging_utils import get_std_logger
        #logger = get_std_logger()
        return RegisteringWorkerPool()
           
    def Test_map_nothing_happens_without_workers(self):
        pool = self._create_pool()
        with pool:
            def f(i): 
                return i
    
            g = gevent.spawn(lambda: pool.map(f,range(1)))
            
            #Assert that no answer will be gotten in the pool map.
            self.assertRaises(gevent.hub.LoopExit, g.join) #"LoopExit: This operation would block forever."
            
            self.assertFalse(g.ready())
            g.kill()

    def Test_map_works_with_workers(self):
        pool = self._create_pool()
        with pool:
            def identity(i):
                if i==0: gevent.sleep(0) #yield before returning the results. Checking that the order of the results is correct anyways.
                return i
            ws = [Worker() for _ in range(2)]
            for w in ws: 
                pool.register_worker(w) 
            inseq = range(10)
            res = pool.map(identity,inseq)
            self.assertSequenceEqual([r.value for r in res], inseq)
        self.assert_(pool.closed.is_set())
        for w in ws: 
            self.assert_(w.closed.is_set())
            
    def Test_map_works_exceptions(self):
        for worker_waiting_at_start in [True, False]:
            print("Testing with worker waiting at start: " + str(worker_waiting_at_start))
            pool = self._create_pool()
            with pool:
                def error_message(i):
                    return "Exception " + str(i)
                def f(i):
                    if i%2 == 0:
                        raise Exception(error_message(i))
                    return i
                
                gevent.spawn(lambda:pool.register_worker(Worker()))
                if worker_waiting_at_start:
                    gevent.sleep(0.001) #yield this thread, let worker start
                
                inseq = range(10)
                res = pool.map(f,inseq)
                
                for i in inseq:
                    if i%2 == 0:
                        self.assert_(res[i].exception)
                        self.assertEqual(res[i].exception.message, error_message(i))
                    else:
                        self.assertEqual(res[i].value, i)
    #TODO: check exception throwing function in map
        
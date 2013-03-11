from __future__ import print_function
import unittest
import gevent
from ..utils.gevent_utils import IterableQueue
from ..utils import ScopedObject

__all__ = []

__all__.append("Worker")
class Worker(ScopedObject):
    def run(self, task):
        result = apply(task,[])
        return result


__all__.append("RegisteringWorkerPool")
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
        #Start a greenlet that puts the worker to work, runing tasks from the queue
        g = gevent.Greenlet(self._run_tasks_from_queue, worker)
        self.working_greenlets.put(g)
        g.start()
        
    def _run_tasks_from_queue(self, worker):
        try:
            for (task,async_result) in self.tasks_with_result_slots_queue:
                try:
                    result = worker.run(task)
                    async_result.set(result)
                except Exception as e:
                    #self.logger.error("Error when trying to execute task {} by worker {}\n{}".format(task, worker, traceback.format_exc()))
                    async_result.set_exception(e)
                #print "Done   " + workerEndpoint + " to run " + str(task)
        finally:
            worker.close()
    
    def map(self, f, items):
        def make_call(f, item): 
            return (lambda: f(item))
        tasks_and_results = [(make_call(f,item), gevent.event.AsyncResult()) for item in items]
        self.tasks_with_result_slots_queue.put_many(tasks_and_results)
        for (item,async_result) in tasks_and_results:
            async_result.wait()
        results = [r for (_,r) in tasks_and_results]
        return results


class RegisteringWorkerPoolTests(unittest.TestCase):
    @staticmethod
    def _create_pool():
        return RegisteringWorkerPool()
           
    def Test_map_without_workers(self):
        pool = self._create_pool()
        with pool:
            def f(i): 
                print("Ran task " + str(i))
                return i
            g = gevent.spawn(lambda: pool.map(f,range(1)))
            #Assert that no answer will be gotten in the pool map.
            self.assertRaises(gevent.hub.LoopExit, g.join) #"LoopExit: This operation would block forever."
            self.assertFalse(g.ready())
            g.kill()

    def Test_map_with_workers(self):
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
        print()
        for worker_waiting_at_start in [True, False]:
            print("Testing with (worker waiting at start: " + str(worker_waiting_at_start) + ")")
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

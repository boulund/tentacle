from __future__ import print_function

from zerorpc_utils import create_server, run_single_rpc
#from multiprocessing import Process, Pipe, JoinableQueue
import gevent
import zerorpc
import sys
import random
import traceback
from utils import printer, dequeueingIteration, Scope, start_logging


#from collections import namedtuple

#ExceptionDescription = namedtuple("ExceptionDescription", ["exc_type", "exc_value", "traceback"])

#class ZeroRpcWorkersRegistryService:

from gevent.queue import Queue, JoinableQueue
from gevent_utils import IterableQueue
gevent.monkey.patch_subprocess()


class ScopedObject(object):
    def __init__(self):
        self._scope = Scope()
        self._scope.__enter__()
    def __enter__(self): 
        pass
    def __exit__(self, exc_type, exc_value, traceback):
        self._scope.__exit__(exc_type, exc_value, traceback)
    def close(self):
        self.__exit__(None,None,None)
             
class WorkerProxy(ScopedObject, zerorpc.Client):
    def __init__(self, workerEndpoint):
        super(WorkerProxy, self).__init__()
        #On close: Close the connection
        self._scope.on_exit(lambda:zerorpc.Client.close(self))
        #Do connect
        self.client.connect(workerEndpoint)
        #On close: Send a close call to the worker side. 
        #Note that on_exit methods are run in reverse order, so this happens before closing the connection above.
        self._scope.on_exit(self("close"))
                       
class WorkerTeam(ScopedObject):
    def __init__(self):
        super(WorkerTeam, self).__init__()
        self.jobs_and_results = IterableQueue()
        self.workers = IterableQueue()
        self.scope.on_exit(lambda: self.workers.close(),
                           lambda: self.jobs_and_results.close(),
                           lambda: [w.close() for w in self.workers])

    def register_worker(self, worker):
        #Start a greenlet that puts the worker to work, processing jobs from the queue
        gevent.spawn(self._process_jobs_from_queue, worker)
        
    def _process_jobs_from_queue(self, worker):
        with worker:
            for (job,async_result) in self.jobs_and_results:
                #print "Asking " + workerEndpoint + " to process " + str(job)
                try:
                    async_result.set(worker.process(job))
                except Exception as e:
                    self.logger.error("Error when trying to execute job {} by worker {}\n{}".format(job, worker, extra=traceback.format_exc()))
                    async_result.set_exception(e)
                #print "Done   " + workerEndpoint + " to process " + str(job)
        print("Worker {} ended gracefully".format(worker))
    
    def process(self, jobs):
        jobs_and_results = [(job, gevent.event.AsyncResult()) for job in jobs]
        for item in jobs_and_results: self.jobs.putMany(item)
        for (job,async_result) in jobs_and_results:
            async_result.wait()
        return jobs_and_results
    
class ZeroRpcWorkersProxy(object):
    #inspired by http://www.gevent.org/gevent.queue.html
    def __init__(self, logger):
        self.logger = logger
        
    def process(self, jobs):
        with Scope() as scope:
            self.jobs = JoinableQueue()
            for item in jobs:
                self.jobs.put(item)

            self.spawned_workers = Queue()
                
            self.logger.info("Starting ZeroRpcWorkersProxy server")
            s, addresses = create_server(self)
            for addr in addresses:
                print(addr)
            gevent.spawn(s.run)
            scope.on_exit(s.stop)
            
            #Wait for the jobs to be completed
            self.jobs.join()
            
            #Wait for all workers to have cleaned up
            for w in dequeueingIteration(self.spawned_workers):
                w.join()       
        
    def _processJobs(self, workerEndpoint):
        try:
            with Scope() as scope:
                workerProxy = zerorpc.Client()
                scope.on_exit(workerProxy.close)

                workerProxy.connect(workerEndpoint)
                scope.on_exit(printer("Exiting, closing worker " + workerEndpoint), 
                              workerProxy.close, 
                              printer("Closed worker " + workerEndpoint))
            
                for job in dequeueingIteration(self.jobs):
                    try:
                        #print "Asking " + workerEndpoint + " to process " + str(job)
                        workerProxy.process(job)
                        #print "Done   " + workerEndpoint + " to process " + str(job)
                    finally:
                        self.jobs.task_done()
        except Exception:
            self.logger.error("Error when trying to execute jobs by worker at {}\n{}".format(workerEndpoint, extra=traceback.format_exc()))
        print("{} ended gracefully".format(workerEndpoint))

    def register_worker(self, workerEndpoint):
        print("Registering worker {}".format(workerEndpoint))
        g = gevent.spawn(self._processJobs, workerEndpoint)
        self.spawned_workers.put(g)
        return "Registered as worker nr {}".format(self.spawned_workers.qsize())

class ZeroRpcMasterProxy(object):
    def __init__(self, logger, masterEndpoint):
        self.logger = logger
        self.masterEndpoint = masterEndpoint
    def register_worker(self, worker):
        try:
            with Scope() as scope:
                #Create the worker service.     
                worker_service, addresses = create_server(worker)
                for addr in addresses:
                    print(addr)
                addr = addresses[0]
                
                #Start the worker service in a separate greenlet (thread) and make sure it is stopped when the scope ends.
                gevent.spawn(worker_service.run)
                scope.on_exit(worker_service.stop)

                #Register the worker service at the master.
                print(run_single_rpc(self.masterEndpoint, 
                                     lambda remote_master: remote_master.register_worker(addr)))
                
                #Wait for the worker to be done, which happens when it is closed by the master.
                worker.done.wait()
        except Exception:
            self.logger.error("Error when trying to work for {}\n{}".format(self.masterEndpoint, traceback.format_exc()))    
           
class BaseWorker(object):
    def __init__(self):
        self.done = gevent.event.Event()
    def close(self):
        self.done.set()

class IntMasterWorker(object):
    class Master:
        def __init__(self, item_count):
            self.item_count = item_count
        def get_jobs(self):
            return range(self.item_count)
    class Worker(BaseWorker):
        def process(self, i):
            t = 1#random.randint(0,10)/10
            print("Processing {}  (sleeping for {}s)".format(i,t))
            gevent.sleep(t)
            print("Done processing " + str(i))
            

if __name__=="__main__":
    logfile = "logfile_" + str(random.randint(0,60000)) + ".log"
    print("Logging to logfile " + logfile)
    logger = start_logging(False, logfile)
            
    if sys.argv[1]=="m":
        logger.info("Starting up as master")
        master = IntMasterWorker.Master(10)
        workersProxy = ZeroRpcWorkersProxy(logger)
        workersProxy.process(master.get_jobs())
    else:
        masterAddress = sys.argv[2]
        logger.info("Starting up as worker for " + masterAddress)
        masterProxy = ZeroRpcMasterProxy(logger, masterAddress)
        masterProxy.register_worker(IntMasterWorker.Worker())

    logger.info("Done")

#create jobs, putMany in queue
#register MasterServer
#
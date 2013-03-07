from __future__ import print_function

#from multiprocessing import Process, Pipe, JoinableQueue
import sys
import random
import traceback

import gevent
import zerorpc
from gevent.queue import Queue, JoinableQueue

from ..zerorpc_utils import spawn_server, run_single_rpc
from ..utils import printer, dequeueingIteration, Scope, start_logging, ScopedObject

                           
class ZeroRpcWorkersProxy(object):
    #inspired by http://www.gevent.org/gevent.queue.html
    def __init__(self, logger):
        self.logger = logger
        
    def process(self, tasks):
        with Scope() as scope:
            self.tasks = JoinableQueue()
            for item in tasks:
                self.tasks.put(item)

            self.spawned_workers = Queue()
                
            self.logger.info("Starting ZeroRpcWorkersProxy server")
            s, addresses = spawn_server(self)
            for addr in addresses:
                print(addr)
            gevent.spawn(s.run)
            scope.on_exit(s.stop)
            
            #Wait for the tasks to be completed
            self.tasks.join()
            
            #Wait for all workers to have cleaned up
            for w in dequeueingIteration(self.spawned_workers):
                w.join()       
        
    def _processtasks(self, workerEndpoint):
        try:
            with Scope() as scope:
                workerProxy = zerorpc.Client()
                scope.on_exit(workerProxy.close)

                workerProxy.connect(workerEndpoint)
                scope.on_exit(printer("Exiting, closing worker " + workerEndpoint), 
                              workerProxy.close, 
                              printer("Closed worker " + workerEndpoint))
            
                for task in dequeueingIteration(self.tasks):
                    try:
                        #print "Asking " + workerEndpoint + " to process " + str(task)
                        workerProxy.process(task)
                        #print "Done   " + workerEndpoint + " to process " + str(task)
                    finally:
                        self.tasks.task_done()
        except Exception:
            self.logger.error("Error when trying to execute tasks by worker at {}\n{}".format(workerEndpoint, extra=traceback.format_exc()))
        print("{} ended gracefully".format(workerEndpoint))

    def register_worker(self, workerEndpoint):
        print("Registering worker {}".format(workerEndpoint))
        g = gevent.spawn(self._processtasks, workerEndpoint)
        self.spawned_workers.put(g)
        return "Registered as worker nr {}".format(self.spawned_workers.qsize())


class ZeroRpcRegisteringWorkerPoolProxy(object):
    def __init__(self, logger, masterEndpoint):
        self.logger = logger
        self.masterEndpoint = masterEndpoint
    def register_worker(self, worker):
        try:
            with Scope() as scope:
                #Create the worker service.     
                worker_service, addresses = spawn_server(worker)
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
        def get_tasks(self):
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
        workersProxy.process(master.get_tasks())
    else:
        masterAddress = sys.argv[2]
        logger.info("Starting up as worker for " + masterAddress)
        masterProxy = ZeroRpcMasterProxy(logger, masterAddress)
        masterProxy.register_worker(IntMasterWorker.Worker())

    logger.info("Done")

#create tasks, putMany in queue
#register MasterServer
#
#  Copyright (C) 2014  Fredrik Boulund and Anders Sjögren
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
from __future__ import print_function
import os
import argparse
import unittest
import gevent
import socket
from datetime import datetime
from .launchers import GeventLauncher
from ..utils.gevent_utils import IterableQueue
from ..utils import ScopedObject
from tentacle.utils.query_jobs_utils import write_jobs_summary


__all__ = []

__all__.append("Worker")
class Worker(ScopedObject):
    def run(self, task):
        result = apply(task,[])
        return result

__all__.append("WorkerDisabledException")
class WorkerDisabledException(Exception):
    """ Raised when master process loses connection to worker node. 
    (e.g. zerorpc.TimeoutExpired or zerorpc.LostRemote) """
    def __init__(self, message):
        self.message = message


__all__.append("RegisteringWorkerPool")
class RegisteringWorkerPool(ScopedObject):
    def __init__(self, output_dir):
        #TODO: Handle errors in init?
        super(RegisteringWorkerPool, self).__init__()
        self.tasks_with_result_slots_queue = IterableQueue()
        self.working_greenlets = IterableQueue()
        self.map_jobs = []
        self.output_dir = output_dir
        self._scope.on_exit(lambda: self.working_greenlets.close(), #close for adding more entries
                            lambda: self.tasks_with_result_slots_queue.close(), #close for adding more entries
                            lambda: [g.join() for g in self.working_greenlets])

    def register_worker(self, worker):
        """ Starts a greenlet that puts the worker to work, running tasks from the queue.
        """
        g = gevent.Greenlet(self._run_tasks_from_queue, worker)
        self.working_greenlets.put(g)
        g.start()
        
    def _run_tasks_from_queue(self, worker):
        """ Run tasks from the queue on the worker.
        """
        def put_failed_job_back_into_queue(self, d, e):
            """ Helper function to put a failed job back into the queue.
            """
            # Everything in this tuple has to be strings, since most objects wont serialize.
            d["attempts"].append((d["worker_name"], str(d["start_time"]), str(e)))
            d["start_time"] = ""
            d["worker_name"] = ""
            if len(d["attempts"]) < 2: #options.maxAttempts:
                self.tasks_with_result_slots_queue.put(d)
            else:
                d["result"].set_exception(e)
            return (self, d)
            
        try:    
            worker_ip = worker._worker_endpoints[0].split("//")[1].split(":")[0]
        except AttributeError:
            worker_ip = "localhost"
        # Here is where the jobs are run
        try:
            for d in self.tasks_with_result_slots_queue:
                try:
                    d["worker_name"] = str(socket.gethostbyaddr(worker_ip)[1][0])
                    d["start_time"] = datetime.now()
                    result = worker.run(d["task"])
                    d["result"].set(result)
                    d["end_time"] = datetime.now()
                except WorkerDisabledException as e:
                    #self.logger.error("Lost connection to Worker with endpoint(s): {}".format(worker._worker_endpoints)) # TODO
                    print("Lost connetion to Worker {} with endpoint(s): {}".format(d["worker_name"], worker._worker_endpoints))
                    self, d = put_failed_job_back_into_queue(self, d, 
                        "Lost connection to Worker {} with endpoint(s) {}".format(d["worker_name"], worker._worker_endpoints))
                    break
                except Exception as e:
                    #self.logger.error("Error when trying to execute task {} by worker {}\n{}".format(description, worker, traceback.format_exc())) # TODO
                    print("Error when trying to execute task '{}' by Worker {}.\n{}.".format(d["description"][0], d["worker_name"], str(e)))
                    self, d = put_failed_job_back_into_queue(self, d, e)

                #self.logger.info("Finished {task} at worker with endpoint(s): {ep}".format(task=task, ep=worker._worker_endpoints))
        finally:
            worker.close()
    
    def map(self, f, items):
        """ Creates a list of tasks and results. """
        def make_call(f, item): 
            return (lambda: f(item))
        tasks_and_results = [{"description":item,
                              "worker_name":"", 
                              "task":make_call(f,item), 
                              "result":gevent.event.AsyncResult(), 
                              "start_time":"", 
                              "end_time":"",
                              "attempts":[]} for item in items]
        self.map_jobs.append(tasks_and_results)
        self.tasks_with_result_slots_queue.put_many(tasks_and_results)
        for job in tasks_and_results:
            job["result"].wait()
        results = [job["result"] for job in tasks_and_results] #pylint: disable=W0601
        self.write_run_summary()
        return results

    def write_run_summary(self):
        """ Writes a complete summary on the status of all jobs after job "completion". """
        summary_filename = "run_summary.txt"
        summary_file = self.output_dir+"/"+summary_filename
        #self.logger.debug("Writing run summary to {}".format(summary_file))
        write_jobs_summary(self.get_mapped_jobs_description(), summary_file)

    def get_mapped_jobs_description(self):
        """ Provides a way to query the status of jobs currently registered with the server."""
        return [[self.describe_task(item) for item in map_job] for map_job in self.map_jobs]

    def describe_task(self, item_entry):
        """ Prepares the information in the job list for serialization. """
        serializable_types = set([str, list, tuple, dict])
        task_description = {}
        for key, value in item_entry.iteritems():
            if type(value) in serializable_types:
                task_description[key] = value
            else:
                task_description[key] = str(value)
        return task_description

__all__.append("GeventWorkerPoolFactory")
class GeventWorkerPoolFactory(object):
    def create_argparser(self):
        parser = argparse.ArgumentParser(add_help=False)
        group = parser.add_argument_group("General distribution options")
        group.add_argument("-N", "--distributionNodeCount", dest="node_count", type=int,
            default=1,
            help="The number of distributed nodes to run on. [default =  %(default)s]")
        parser.add_argument_group(group)
        return parser
    
    def create_from_parsed_args(self, parsed_args, output_dir, *args, **kwargs):
        return self.create(worker_count=parsed_args.node_count, output_dir=output_dir)
    
    def create(self, worker_count, output_dir):
        #Create the pool
        pool = RegisteringWorkerPool(output_dir=output_dir)
        try:
            ws = [Worker() for _ in range(worker_count)]
            for w in ws: 
                pool.register_worker(w) 
        except:
            pool.close()
            raise
        return pool



############################################
#       UNIT TESTS
############################################

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

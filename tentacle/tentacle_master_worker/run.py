#!/usr/bin/env python
from master import *
from worker import * 

__all__ = ["run"]

def run(argv):
    options = TentacleMaster.parse_args(argv)
    master = TentacleMaster()
    worker = TentacleWorker(options)
    
    #run the master
    jobs = master.process(options)
    
    #run the single worker
    for job in jobs:
        worker.process(job)


class SingleWorkerTeam(object):
    def __init__(self, worker):
        self.worker = worker        
        
    def process(self, jobs):
        for job in jobs:
            self.worker.process(job)

###################
#
# MAIN
#
###################
if __name__ == "__main__":
    import sys
    run(sys.argv)
    exit(0)

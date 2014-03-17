#!/usr/bin/env python
from __future__ import print_function
from tentacle.tentacle_master_worker import TentacleMaster, TentacleWorker, LaunchingMasterWorkerExecutor
from tentacle.launching.zero_rpc_worker_pool import ZeroRpcDistributedWorkerPoolFactory
from tentacle.launching.registering_worker_pool import GeventWorkerPoolFactory
from tentacle.launching.launchers import SubprocessLauncher, SlurmLauncher, GeventLauncher
from tentacle.utils.query_jobs_utils import write_job_summary

__all__ = ["run"]

def run(argv, 
        launcher_factory=SubprocessLauncher, 
        distributed_worker_pool_factory=ZeroRpcDistributedWorkerPoolFactory()):
    master_factory = TentacleMaster
    worker_factory = TentacleWorker
    g = LaunchingMasterWorkerExecutor.launch_master_worker(argv, 
                                                           master_factory, 
                                                           worker_factory, 
                                                           launcher_factory, 
                                                           distributed_worker_pool_factory)
    if hasattr(g, 'get'):
        print("Waiting for processing to complete")
        g.get()
    server_address = "tcp://10.21.1.130:49152"
    import os
    print("Writing summary to {}".format(os.getcwd()+"run_summary.txt"))
    write_job_summary(server_address, "run_summary.txt")
    print("Done")

###################
#
# MAIN
#
###################
if __name__ == "__main__":
    import sys
    run(sys.argv, GeventLauncher, GeventWorkerPoolFactory())
    exit(0)

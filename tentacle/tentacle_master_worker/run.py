#!/usr/bin/env python
from __future__ import print_function
from tentacle.tentacle_master_worker import TentacleMaster, TentacleWorker, LaunchingMasterWorkerExecutor
from tentacle.launching.zero_rpc_worker_pool import ZeroRpcDistributedWorkerPoolFactory
from tentacle.launching.registering_worker_pool import GeventWorkerPoolFactory
from tentacle.launching.launchers import SubprocessLauncher, SlurmLauncher, GeventLauncher

__all__ = ["run"]

def run(argv, launcher_factory=SubprocessLauncher, distributed_worker_pool_factory = ZeroRpcDistributedWorkerPoolFactory()):
    master_factory = TentacleMaster
    worker_factory = TentacleWorker
    return LaunchingMasterWorkerExecutor.launch_master_worker(argv, master_factory, worker_factory, launcher_factory, distributed_worker_pool_factory)

###################
#
# MAIN
#
###################
if __name__ == "__main__":
    import sys
    g = run(sys.argv)#, GeventLauncher, GeventWorkerPoolFactory())
    if hasattr(g, 'get'):
        print("Waiting for processing to complete")
        g.get()
        print("Done")
    exit(0)

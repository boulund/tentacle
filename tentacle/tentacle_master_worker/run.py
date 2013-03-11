#!/usr/bin/env python
from tentacle.tentacle_master_worker import TentacleMaster, TentacleWorker, LaunchingMasterWorkerExecutor
from tentacle.launching.zero_rpc_worker_pool import ZeroRpcDistributedWorkerPoolFactory
from tentacle.launching.launchers import SubprocessLauncher, SlurmLauncher, GeventLauncher

__all__ = ["run"]

def run(argv, launcher_factory=GeventLauncher, distributed_worker_pool_factory = ZeroRpcDistributedWorkerPoolFactory()):
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
    run(sys.argv)
    exit(0)

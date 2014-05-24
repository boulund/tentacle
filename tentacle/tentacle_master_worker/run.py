#!/usr/bin/env python
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
from tentacle.tentacle_master_worker import TentacleMaster, TentacleWorker, LaunchingMasterWorkerExecutor
from tentacle.launching.zero_rpc_worker_pool import ZeroRpcDistributedWorkerPoolFactory
from tentacle.launching.registering_worker_pool import GeventWorkerPoolFactory
from tentacle.launching.launchers import SubprocessLauncher, SlurmLauncher, GeventLauncher

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
        #print("Waiting for processing to complete")
        g.get()
    #print("Done")

###################
#
# MAIN
#
###################
if __name__ == "__main__":
    import sys
    run(sys.argv, GeventLauncher, GeventWorkerPoolFactory())
    exit(0)

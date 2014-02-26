#!/usr/bin/env python
# coding: utf-8
#
# Tentacle Parallel (Slurm)
#
# Authors:
#   Anders Sjögren
#   Fredrik Boulund
# 
# Copyright (c) 2014
# 

if __name__ == "__main__":
    from os.path import join, abspath, dirname
    import os
    import sys
    import platform
    import tempfile

    #Add the folder of tentacle to path, to be able to import it
    run_dir = abspath(dirname(__file__))
    base_dir = abspath(join(run_dir,".."))
    sys.path.append(base_dir)
    from tentacle.tentacle_master_worker import TentacleMaster, TentacleWorker, LaunchingMasterWorkerExecutor
    from tentacle.launching.zero_rpc_worker_pool import ZeroRpcDistributedWorkerPoolFactory
    from tentacle.launching.registering_worker_pool import GeventWorkerPoolFactory
    from tentacle.launching.launchers import SubprocessLauncher, SlurmLauncher, GeventLauncher
    from tentacle import run

    #Add the built in dependencies to PATH
    dependencies_bin = os.path.join(base_dir,"dependencies","bin",platform.system())
    os.environ["PATH"]  = dependencies_bin + os.pathsep + os.environ["PATH"] 



    ############################################################
    # 
    #   COPY THIS FILE AND ADD OPTIONS BELOW TO HAVE PERSISTENT 
    #   RUNS SAVED FOR CONVENIENT RE-RUN AND BACKTRACE. 
    #
    ############################################################
    argv = sys.argv + [
            #"--mappingManifest", "",
            #"--pblat"
            #"-N", "2", 
            #"-o", "tentacle_results",
            ]

    run(argv, GeventLauncher, GeventWorkerPoolFactory())
    #run(argv, SubprocessLauncher)

#!/usr/bin/env python
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

def dd(file_name):
    return join(base_dir,"data_gem_human_filter",file_name)

#Add the built in dependencies to PATH
bin_dir = os.path.join(base_dir,"dependencies","bin",platform.system())
os.environ["PATH"]  = os.environ["PATH"]  + os.pathsep + bin_dir

#tmp_dir = tempfile.mkdtemp()
out_dir = join(base_dir,"workdir","tentacle_output")

argv = sys.argv + [
        dd("contigs"), dd("reads"), dd("annotations"), 
        "-o", out_dir,
        "--makeUniqueOutputDirectoryNameIfNeeded", 
        "--deleteTempFiles",
        "--splitCharAnnotations", "_",
        "--splitCharReads", "_",
        "--splitCharReferences", "_",
        "--bowtie2FilterReads",
        "--bowtie2FilterDB", "/home/boulund/workspace/tentacle_human_filter_support/data_gem_human_filter/hg19.tgz",
        #"--blast", 
        #"--pblat",
        #"--razers3",
        "--gem",
        "--gemDBName", "contigs.fa",
        #"-N", "2", 
        "--localCoordinator",
        #"--distributionUseDedicatedCoordinatorNode",
	    #"--distributedNodeIdleTimeout", "30",
        #"--slurmTimeLimit", "8:00:00"
        "--verbose"
        ]

#run(argv, SlurmLauncher)
#exit(0)
run(argv, GeventLauncher, GeventWorkerPoolFactory())
#run(argv, SubprocessLauncher)

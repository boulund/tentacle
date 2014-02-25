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

#Add the built in dependencies to PATH
bin_dir = os.path.join(base_dir,"dependencies","bin",platform.system())
os.environ["PATH"]  = bin_dir + os.pathsep + os.environ["PATH"]

out_dir = join(base_dir,"workdir","plasmidfixes")

argv = sys.argv + [
        "--mappingManifest", "data/manifest.tab",
        "--makeUniqueOutputDirectoryNameIfNeeded",
        "--noQualityControl",
        "--localCoordinator",
        #"--usearch",
        #"--usearchID", "0.9",
        #"--usearchDBName", "bacmet.fasta",
        #"--usearchFilterSequencesShorterThan", "75",
        #"--usearchStrand", "both",
        "--logLevel", "DEBUG",
        "--saveMappingResultsFile",
        "-N", "1",
        "-o", out_dir,
        ]

#run(argv, SlurmLauncher)
#exit(0)
run(argv, GeventLauncher, GeventWorkerPoolFactory())
#run(argv, SubprocessLauncher)

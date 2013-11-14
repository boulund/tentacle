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

def dd(data_dir, resource_dir):
    return join(base_dir, data_dir, resource_dir)

#Add the dependencies directory to PATH
bin_dir = os.path.join(base_dir,"dependencies","bin",platform.system())
os.environ["PATH"]  = os.environ["PATH"]  + os.pathsep + bin_dir


out_dir = join(base_dir,"workdir","tests_output")


general_argv = sys.argv + [
        "-o", out_dir,
        "--makeUniqueOutputDirectoryNameIfNeeded", 
        "--deleteTempFiles",
        "--splitCharAnnotations", "_",
        "--splitCharReads", "_",
        "--splitCharReferences", "_",
        "--localCoordinator",
        #"-N", "2", 
        #"--distributionUseDedicatedCoordinatorNode",
        #"--distributedNodeIdleTimeout", "30",
        #"--slurmTimeLimit", "8:00:00"
        "--verbose"
        ]


##### RAZERS3 ####
razers3_argv = general_argv + [
        dd("tests_data/razers3/", "contigs"), 
        dd("tests_data/razers3/", "reads"), 
        dd("tests_data/razers3/", "annotations"), 
        "--razers3"
        ]
run(razers3_argv, GeventLauncher, GeventWorkerPoolFactory())


##### PBLAT #####
pblat_argv = general_argv + [
        dd("tests_data/pblat/", "contigs"), 
        dd("tests_data/pblat/", "reads"),
        dd("tests_data/pblat/", "annotations"), 
        "--pblat"
        ]
run(pblat_argv, GeventLauncher, GeventWorkerPoolFactory())


##### Bowtie2 #####
bowtie2_argv = general_argv + [
        dd("tests_data/bowtie2/", "reference"), 
        dd("tests_data/bowtie2/", "reads"),
        dd("tests_data/bowtie2/", "annotations"), 
        "--bowtie2",
        "--bowtie2Threads", "8",
        "--bowtie2DBName", "contigs.fasta"
        ]
run(bowtie2_argv, GeventLauncher, GeventWorkerPoolFactory())


##### GEM #####
gem_argv = general_argv + [
        dd("tests_data/gem/", "reference"), 
        dd("tests_data/gem/", "reads"),
        dd("tests_data/gem/", "annotations"), 
        "--gem",
        "--gemDBName", "contigs.fasta"
        ]
run(gem_argv, GeventLauncher, GeventWorkerPoolFactory())


##### USEARCH #####
usearch_argv = general_argv + [
        dd("tests_data/usearch/", "reference"), 
        dd("tests_data/usearch/", "reads"),
        dd("tests_data/usearch/", "annotations"), 
        "--usearch",
        "--usearchDBName", "contigs.fasta",
        "--usearchStrand", "both",
        ]
run(usearch_argv, GeventLauncher, GeventWorkerPoolFactory())


#!/usr/bin/env python
from os.path import join, abspath, dirname
import os
import sys
import platform
import tempfile
import unittest

#Add the folder of tentacle to path, to be able to import it
run_dir = abspath(dirname(__file__))
base_dir = abspath(join(run_dir,".."))
sys.path.append(base_dir)

from tentacle.tentacle_master_worker import TentacleMaster, TentacleWorker, LaunchingMasterWorkerExecutor
from tentacle.launching.zero_rpc_worker_pool import ZeroRpcDistributedWorkerPoolFactory
from tentacle.launching.registering_worker_pool import GeventWorkerPoolFactory
from tentacle.launching.launchers import SubprocessLauncher, SlurmLauncher, GeventLauncher
from tentacle import run

#Add the dependencies directory to PATH
bin_dir = os.path.join(base_dir,"dependencies","bin",platform.system())
os.environ["PATH"]  = bin_dir + os.pathsep + os.environ["PATH"]


class Test_complete_pipelines(unittest.TestCase):

    def setUp(self):
        self.out_dir = join(base_dir,"workdir","tests_output")

        self.general_argv = sys.argv + [
                "-o", self.out_dir,
                "--makeUniqueOutputDirectoryNameIfNeeded", 
                #"--noQualityControl",
                #"--deleteTempFiles",
                "--splitCharAnnotations", "_",
                "--splitCharReads", "_",
                "--splitCharReferences", "_",
                "--localCoordinator",
                #"-N", "2", 
                #"--distributionUseDedicatedCoordinatorNode",
                #"--distributedNodeIdleTimeout", "30",
                #"--slurmTimeLimit", "8:00:00"
                "--logLevel", "DEBUG"
                ]

##    def tearDown(self):
##        import shutil
##        shutil.rmtree(self.out_dir)
##
#    def test_razers3(self):
#        ##### RAZERS3 ####
#        razers3_argv = self.general_argv + [
#                "--razers3",
#                "--mappingManifest", "tests_data/razers3/mappingManifest.tab",
#                ]
#        run(razers3_argv, GeventLauncher, GeventWorkerPoolFactory())
#
#    def test_pblat(self):
#        ##### PBLAT #####
#        pblat_argv = self.general_argv + [
#                "--pblat",
#                "--mappingManifest", "tests_data/pblat/mappingManifest.tab",
#                ]
#        run(pblat_argv, GeventLauncher, GeventWorkerPoolFactory())
#
#
#    def test_bowtie2(self):
#        ##### Bowtie2 #####
#        bowtie2_argv = self.general_argv + [
#                "--bowtie2",
#                "--bowtie2Threads", "8",
#                "--bowtie2DBName", "contigs.fasta",
#                "--mappingManifest", "tests_data/bowtie2/mappingManifest.tab",
#                ]
#        run(bowtie2_argv, GeventLauncher, GeventWorkerPoolFactory())
#
#    def test_gem(self):
#        ##### GEM #####
#        gem_argv = self.general_argv + [
#                "--gem",
#                "--gemDBName", "contigs.fasta",
#                "--mappingManifest", "tests_data/gem/mappingManifest.tab",
#                ]
#        run(gem_argv, GeventLauncher, GeventWorkerPoolFactory())

    def test_usearch(self):
        ##### USEARCH #####
        usearch_argv = self.general_argv + [
                "--usearch",
                "--usearchDBName", "contigs.fasta",
                "--usearchStrand", "both",
                "--mappingManifest", "tests_data/mappingManifest.tab",
                ]
        run(usearch_argv, GeventLauncher, GeventWorkerPoolFactory())


if __name__ == "__main__":
    unittest.main(buffer=False)

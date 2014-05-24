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
from os.path import join, abspath, dirname
import os
import sys
import platform
import tempfile
import unittest

try:
    from tentacle.tentacle_master_worker import TentacleMaster, TentacleWorker, LaunchingMasterWorkerExecutor
    from tentacle.launching.zero_rpc_worker_pool import ZeroRpcDistributedWorkerPoolFactory
    from tentacle.launching.registering_worker_pool import GeventWorkerPoolFactory
    from tentacle.launching.launchers import SubprocessLauncher, SlurmLauncher, GeventLauncher
    from tentacle import run
except ImportError:
    # If import fails Tentacle is probably not installed in 
    # python site-packages. Try to run it from the 
    # current directory instead.
    # Add TENTACLE_ROOT to PATH to be able to import Tentacle
    run_dir = dirname(os.path.realpath(__file__))
    base_dir = abspath(join(run_dir,".."))
    os.environ["PATH"] = base_dir + os.pathsep + os.environ["PATH"]
    sys.path.insert(1, base_dir)
    try:
        from tentacle.tentacle_master_worker import TentacleMaster, TentacleWorker, LaunchingMasterWorkerExecutor
        from tentacle.launching.zero_rpc_worker_pool import ZeroRpcDistributedWorkerPoolFactory
        from tentacle.launching.registering_worker_pool import GeventWorkerPoolFactory
        from tentacle.launching.launchers import SubprocessLauncher, SlurmLauncher, GeventLauncher
        from tentacle import run
    except ImportError:
        print "ERROR: Cannot import/find Tentacle, is it properly installed?"
        print "If you're trying to run Tentacle without installing, make sure to"
        print "run it from within the %TENTACLE_ROOT%/rundir directory."
        exit()
    # Add the Tentacle dependencies directory to PATH 
    dependencies_bin = join(base_dir,"dependencies","bin",platform.system())
    os.environ["PATH"] += os.pathsep + dependencies_bin
    sys.path.append(dependencies_bin)


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
                "--logLevel", "CRITICAL"
                ]

    def tearDown(self):
        import shutil
        shutil.rmtree(self.out_dir)

    def test_razers3(self):
        ##### RAZERS3 ####
        razers3_argv = self.general_argv + [
                "--razers3",
                "--mappingManifest", "tests_data/mappingManifest.tab",
                ]
        run(razers3_argv, GeventLauncher, GeventWorkerPoolFactory())

    def test_pblat(self):
        ##### PBLAT #####
        pblat_argv = self.general_argv + [
                "--pblat",
                "--mappingManifest", "tests_data/mappingManifest.tab",
                ]
        run(pblat_argv, GeventLauncher, GeventWorkerPoolFactory())


    def test_bowtie2(self):
        ##### Bowtie2 #####
        bowtie2_argv = self.general_argv + [
                "--bowtie2",
                "--bowtie2Threads", "8",
                "--bowtie2DBName", "contigs.fasta",
                "--mappingManifest", "tests_data/mappingManifest.tab",
                ]
        run(bowtie2_argv, GeventLauncher, GeventWorkerPoolFactory())

    def test_gem(self):
        ##### GEM #####
        gem_argv = self.general_argv + [
                "--gem",
                "--gemDBName", "contigs.fasta",
                "--mappingManifest", "tests_data/mappingManifest.tab",
                ]
        run(gem_argv, GeventLauncher, GeventWorkerPoolFactory())

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
    unittest.main(buffer=True)

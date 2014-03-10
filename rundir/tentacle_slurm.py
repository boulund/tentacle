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
from os.path import join, abspath, dirname
import os
import sys
import platform

# Add TENTACLE_ROOT to PATH to be able to import Tentacle
run_dir = dirname(os.path.realpath(__file__))
base_dir = abspath(join(run_dir,".."))
os.environ["PATH"] = base_dir + os.pathsep + os.environ["PATH"]
sys.path.insert(1, base_dir)

# Import Tentacle
from tentacle.launching.launchers import SlurmLauncher
from tentacle import run

# Add the Tentacle dependencies directory to PATH 
dependencies_bin = join(base_dir,"dependencies","bin",platform.system())
os.environ["PATH"] += os.pathsep + dependencies_bin
sys.path.append(dependencies_bin)

if __name__ == "__main__":
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
            #"--localCoordinator",
            #"--distributionUseDedicatedCoordinatorNode",
            #"--distributedNodeIdleTimeout", "30",
            #"--slurmTimeLimit", "00:10:00",
            #"--slurmJobName", "Tentacle",
            ]

    run(argv, SlurmLauncher)
    exit(0)

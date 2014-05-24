#!/usr/bin/env python
# coding: utf-8
#
# Tentacle Parallel (Slurm)
#
# Authors:
#   Anders Sjögren
#   Fredrik Boulund
# 
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
# 
from os.path import join, abspath, dirname
import os
import sys
import platform

try:
    from tentacle.launching.launchers import SlurmLauncher
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
        from tentacle.launching.launchers import SlurmLauncher
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

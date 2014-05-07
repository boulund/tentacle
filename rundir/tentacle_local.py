#!/usr/bin/env python
# coding: utf-8
#
# Tentacle Local (GeventLauncher)
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
import tempfile

try:
    from tentacle.launching.launchers import GeventLauncher, SubprocessLauncher
    from tentacle.launching.registering_worker_pool import GeventWorkerPoolFactory
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
        from tentacle.launching.launchers import GeventLauncher, SubprocessLauncher
        from tentacle.launching.registering_worker_pool import GeventWorkerPoolFactory
        from tentacle import run
    except ImportError,e :
        print "ERROR: Cannot import/find Tentacle, is it properly installed?"
        print "If you're trying to run Tentacle without installing, make sure to"
        print "run it from within the %TENTACLE_ROOT%/rundir directory."
        print e
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
            ]

    run(argv, GeventLauncher, GeventWorkerPoolFactory())
    #run(argv, SubprocessLauncher)

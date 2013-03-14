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
    return join(base_dir,"dist_data",file_name)

#Add the built in dependencies to PATH
bin_dir = os.path.join(base_dir,"dependencies","bin",platform.system())
os.environ["PATH"]  = os.environ["PATH"]  + os.pathsep + bin_dir

tmp_dir = tempfile.mkdtemp()
out_dir = join(tmp_dir,"tentacle_output")
print("Saving results to temp dir: " + out_dir)

argv = ["",
        dd("contigs"), dd("reads"), dd("annotations"), 
        "--makeUniqueOutputDirectoryNameIfNeeded", 
        "--pblat", 
        "-N", "2", 
        "--localCoordinator",
        "-o", out_dir
        ]
run(argv, GeventLauncher, GeventWorkerPoolFactory())

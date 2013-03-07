from __future__ import print_function

import argparse
from subprocess import PIPE, Popen
import unittest

from .. import utils

__all__ = ["SlurmLauncher"]

default_tentacle_slurm_options = ({"slurmPartition":"glenn", "slurmAccount":"SNIC001-12-175", "slurmJobName":"TentacleTest", "slurmTimeLimit":"1:00:00"})

class Launcher(object):
    @staticmethod
    def create_python_function_command(f):
        import base64
        import cloud.serialization
        import zlib
        python_prog_template = "import base64; import cloud.serialization; import zlib; f=cloud.serialization.deserialize(zlib.decompress(base64.b64decode('{0}'))); f();"
        encoded_cmd = base64.b64encode(zlib.compress(cloud.serialization.serialize(f,True),9))
        python_prog = python_prog_template.format(encoded_cmd)
        return "python -c \"{}\"".format(python_prog)
    
    def launch_python_function(self, f, options=default_tentacle_slurm_options, additional_slurm_args=[]):
        commands = [
            #load python module, activate virtual_env, add libs dir to LD_PATH
            '. /c3se/NOBACKUP/groups/c3-snic001-12-175/activate_python', #TODO: remove hard-coded action. Make configurable.
            self.create_python_function_command(f) ]
        return self.launch(commands, options, additional_slurm_args)


class SlurmLauncher(Launcher):
    @staticmethod
    def create_launch_options_argparser():
        parser = argparse.ArgumentParser(add_help=False)
        group = parser.add_argument_group("SLURM optiona", "Options for the distributed computing though SLURM")
        group.add_argument("--slurmNodes",
            type=int, default=10, 
            help="The total number of slurm nodes to run, divided into different SLURM jobs. [default: %(default)s]")
    #    group.add_argument("--slurmNodesPerJob",
    #        type=int, default=1, 
    #        help="The N option for sbatch. [default: %(default)s]")
        group.add_argument("--slurmPartition",
            default="glenn", #TODO: Remove this hardcoded default, move into config file for easy access
            help="The P option for sbatch. [default: %(default)s]")
        group.add_argument("--slurmAccount",
            default="SNIC001-12-175", 
            help="The A option for sbatch. [default: %(default)s]")
        group.add_argument("--slurmJobName",
            default="Tentacle",
            help="The J option for sbatch. [default: %(default)s]")    
        group.add_argument("--slurmTimeLimit",
            default="1:00:00",
            help="The t option for sbatch. [default: %(default)s]")    
        return parser
    
    @staticmethod
    def create_sbatch_script(commands, options):
        setupStr = ("\n".join(["#!/usr/bin/env bash",
                               "#SBATCH -N {slurmNodesPerJob}",
                               "#SBATCH -p {slurmPartition}",
                               "#SBATCH -A {slurmAccount}",
                               "#SBATCH -J {slurmJobName}",
                               "#SBATCH -o {slurmJobName}%j_%n.stdout", #TODO: add customisable stdout dir
                               "#SBATCH -e {slurmJobName}%j_%n.stderr", #TODO: add customisable stderr dir
                               "#SBATCH -t {slurmTimeLimit}",
                               ""])).format(slurmNodesPerJob=1, **options)
        jobsStr = "\n".join(commands)
        return setupStr + jobsStr
    
    def launch(self, commands, options=default_tentacle_slurm_options, additional_slurm_args=[]):
        script = self.create_sbatch_script(commands, options)
        call_pars = ["ssh", "glenn", "sbatch"] #TODO: Change back to [utils.resolve_executable("sbatch")], or add configurability.
        call_pars.extend(additional_slurm_args)
        print("launching: " + " ".join(call_pars) + " with input " + script)
        #Make the sbatch call
        (out, err) = Popen(call_pars, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate(script)
        return (out, err)


class test(unittest.TestCase):
    def test_empty(self):
        sl = SlurmLauncher()
        print(sl.launch_python_function(lambda: print("yes!")))

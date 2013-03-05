from __future__ import print_function

import argparse
from subprocess import PIPE, Popen
import unittest

from .. import utils

__all__ = ["SlurmLauncher"]

class SlurmLauncher(object):
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
        setupStr = ("\n".join(["#!/usr/bin/env bash"
                               "#SBATCH -N {slurmNodesPerJob}"
                               "#SBATCH -p {slurmPartition}"
                               "#SBATCH -A {slurmAccount}"
                               "#SBATCH -J {slurmJobName}"
                               "#SBATCH -o %j_%n.stdout"
                               "#SBATCH -e %j_%n.stderr"
                               "#SBATCH -t {slurmTimeLimit}"
                               ""])).format(slurmNodesPerJob=1, **options)
        jobsStr = "\n".join(commands)
        print(setupStr + jobsStr)
        return setupStr + jobsStr
    
    def launch(self, commands, options, additional_slurm_args = []):
        script = self.create_sbatch_script(commands, options)
        call_pars = [utils.resolve_executable("sbatch")]
        call_pars.extend(additional_slurm_args)
        print("launching: " + " ".join(call_pars) + " with input " + script)
        #Make the sbatch call
        (out, err) = Popen(call_pars, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate(script)
        print(out)
        print(err)
    
    @staticmethod
    def create_python_function_command(f):
        import base64
        import cloud.serialization
        python_prog_template = "import base64; import cloud.serialization; f=cloud.serialization.deserialize(base64.b64decode('{0}')); f();"
        base64_serialized_cmd = base64.b64encode(cloud.serialization.serialize(f,True))
        python_prog = python_prog_template.format(base64_serialized_cmd)
        return "python -c \"{}\"".format(python_prog)
    
    def launch_python_function(self, f, options, additional_slurm_args):
        commands = [
            '. /c3se/NOBACKUP/groups/c3-snic001-12-175/activate_python', #load python module, activate virtual_env, add libs dir to LD_PATH
            self.create_python_function_command(f) ]
        self.launch(commands, options, additional_slurm_args)

#class test(unittest.TestCase):
#    def test_empty(self):
#        sl = SlurmLauncher()
#        sl.launch_python_function(lambda: print("yes!"),({"slurmPartition":"glenn", "slurmAccount":"001-012-175", "slurmJobName":"TentacleTest", "slurmTimeLimit":"1:00"}),({}))

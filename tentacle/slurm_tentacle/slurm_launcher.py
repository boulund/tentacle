import argparse
from subprocess import PIPE, Popen

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
            default="glenn",
            help="The P option for sbatch. [default: %(default)s]")
        group.add_argument("--slurmAccount",
            required=True,
            help="REQUIRED: The A option for sbatch.")
        group.add_argument("--slurmJobName",
            required=True,
            help="REQUIRED: The J option for sbatch.")    
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
        return setupStr + jobsStr
    
    def launch(self, commands, options, additional_slurm_args = []):
        script = self.create_sbatch_script(commands, options)
        call_pars = [utils.resolve_executable("sbatch")]
        call_pars.extend(additional_slurm_args)
        (out, err) = Popen(call_pars, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate(script)
        print

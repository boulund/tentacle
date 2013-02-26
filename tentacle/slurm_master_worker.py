import argparse

def create_slurm_argparser():
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

def create_sbatch_script(commands, options):
    setupStr = ("\n".join(["#!/usr/bin/env bash"
                           "#SBATCH -N {slurmNodesPerJob}"
                           "#SBATCH -p {slurmPartition}"
                           "#SBATCH -A {slurmAccount}"
                           "#SBATCH -J {slurmJobName}"
                           "#SBATCH -o my.stdout"
                           "#SBATCH -t {slurmTimeLimit}"
                           ""])).format(slurmNodesPerJob=1, **options)
    jobsStr = "\n".join(commands)
    return setupStr + jobsStr

def start_slurm_master_worker(argv):
    #TODO: Parse args
    node_count = 10
    account = "001-12-175"
    time_limit = "7-0:0:0" #one week
    #TODO: create and submit master job
    #TODO: create and submit workers jobs
    
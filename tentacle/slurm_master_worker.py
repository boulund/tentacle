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
    pass
    #collect parsers from worker + master + master job desc + output_dir + slurm_opts + logger opts (verbosity)
    #create joint parser and parse to handle help
    #for each parser parse output, to get fine-grained options
    #create result_dir (and subdirs), with name from options
    #serialize opts into output/communication/options
    #create master and worker slurm scripts, with slurm_opts
    #launch master and worker with output_dir as argument, from where they can access the communication and result dirs

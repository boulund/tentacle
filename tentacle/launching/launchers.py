from __future__ import print_function
import argparse
import os.path
import random
import shlex
from subprocess import PIPE
import sys
import unittest
import gevent
from gevent.subprocess import Popen
from tentacle import utils
from ..utils.zerorpc_utils import join_all_greenlets

gevent.monkey.patch_subprocess()

__all__ = []

def create_python_function_command(f):
    import base64
    import cloud.serialization
    import zlib
    python_prog_template = "import base64; import cloud.serialization; import zlib; f=cloud.serialization.deserialize(zlib.decompress(base64.b64decode('{0}'))); f();"
    encoded_cmd = base64.b64encode(zlib.compress(cloud.serialization.serialize(f,True),9))
    python_prog = python_prog_template.format(encoded_cmd)
    return "python -c \"{}\"".format(python_prog)

def create_main_function_wrapper(f, join_all_greenlets_at_end=True):
    def main():
        f()
        if join_all_greenlets_at_end:
            join_all_greenlets(timeout=20)
    return main
            

__all__.append("Launcher")
class Launcher(object):
    def launch_python_function(self, f):
        raise Exception("Abstract function not implemented.")
    
    @classmethod
    def create_argparser(cls):
        return argparse.ArgumentParser(add_help=False)

    @classmethod
    def create_from_parsed_args(cls, stdio_dir, parsed_args):
        return cls(stdio_dir, parsed_args)
    
    def __init__(self, stdio_dir=".", parsed_args=argparse.Namespace()):
        self.stdio_dir = stdio_dir
        self.parsed_args = parsed_args


__all__.append("GeventLauncher")
class GeventLauncher(object):
    @classmethod
    def create_argparser(cls):
        return argparse.ArgumentParser(add_help=False)

    @classmethod
    def create_from_parsed_args(cls, parsed_args, *args, **kwargs):
        return cls()

    def launch_python_function(self, f):
        return gevent.spawn(f)
        

__all__.append("SubprocessLauncher")
class SubprocessLauncher(Launcher):
    def launch_python_function(self, f, join_all_greenlets_at_end=True): #TODO: add file_paths to config
        main_f = create_main_function_wrapper(f)
        cmd = create_python_function_command(main_f)
        call_pars = shlex.split(cmd)
        rand_id = random.randint(0, sys.maxint)
        stdout_file_path = os.path.join(self.stdio_dir, hex(rand_id)+"_stdout.log")
        stderr_file_path = os.path.join(self.stdio_dir, hex(rand_id)+"_stderr.log")
        stdout_file = open(stdout_file_path, "w")
        stderr_file = open(stderr_file_path, "w")
        #TODO: Close files on failure. Use: scope.on_exception
        g = gevent.spawn(Popen(call_pars,stdout=stdout_file,stderr=stderr_file).communicate)
        g.link(lambda _: stdout_file.close())
        g.link(lambda _: stderr_file.close())
        return g


__all__.append("SlurmLauncher")    
class SlurmLauncher(Launcher):
    @classmethod
    def create_argparser(cls):
        parser = argparse.ArgumentParser(add_help=False)
        group = parser.add_argument_group("SLURM options", "Options for the distributed computing through SLURM")
        group.add_argument("--slurmPartition",
            default="glenn", #TODO: Remove this hardcoded default, move into config file for easy access
            help="The P option for sbatch. [default: %(default)s]")
        group.add_argument("--slurmAccount",
            default="SNIC2013-1-191", 
            help="The A option for sbatch. [default: %(default)s]")
        group.add_argument("--slurmJobName",
            default="Tentacle",
            help="The J option for sbatch. [default: %(default)s]")    
        group.add_argument("--slurmTimeLimit",
            default="1:00:00",
            help="The t option for sbatch. [default: %(default)s]")
        group.add_argument("--slurmMem",
            default="SMALLMEM",
            help="The C option for sbatch. Example SMALLMEM/BIGMEM/HUGEMEM [default: %(default)s]")
        group.add_argument("--slurmNodesPerJob",
            default="1", 
            help="Number of nodes in each slurm call [default: %(default)s]")
#        group.add_argument("--slurmExtraOptions",
#            default="",
#            help="Any extra options to be sent to the SLURM sbatch command. [default: %(default)s]") #TODO: Implement.
        group.add_argument("--slurmStdOut",
            default="{slurmJobName}%j_%n.stdout", 
            help="The name of the saved standard output file from when slurm has run. Will be placed in a stdio-directory. [default: %(default)s]")
        group.add_argument("--slurmStdErr",
            default="{slurmJobName}%j_%n.stderr", 
            help="The name of the saved standard error file from when slurm has run. Will be placed in a stdio-directory. [default: %(default)s]")
#        group.add_argument("--slurmSetupCommands",
#            default='. /c3se/NOBACKUP/groups/c3-snic001-12-175/activate_python',
#            help="A command to be executed by the shell, e.g. to activate the proper version of python. [default: %(default)s]")
        sbatch_bin = utils.resolve_executable("sbatch", "sbatch not found!")
        group.add_argument("--slurmBinary",
            default=sbatch_bin,
            #required=(sbatch_bin == "sbatch not found!"),
            help="The binary for executing sbatch. May also e.g. use \"ssh remote sbatch\" for starting on a remote cluster. [default: %(default)s]")
        return parser
    
    @classmethod
    def create_sbatch_script(cls, commands, stdio_dir, parsed_args):
        parsed_args_dict = parsed_args.__dict__
        stdout_file_name = parsed_args.slurmStdOut.format(**parsed_args_dict)   #Options magic ok in this case : pylint: disable=W0142
        stdout_file_path=os.path.join(stdio_dir,stdout_file_name) 
        stderr_file_name = parsed_args.slurmStdErr.format(**parsed_args_dict)   #Options magic ok in this case : pylint: disable=W0142
        stderr_file_path=os.path.join(stdio_dir,stderr_file_name)
        
        setupTemplate = ("\n".join(["#!/usr/bin/env bash",              #Options magic below ok in this case : #pylint: disable=W0142
                               "#SBATCH -N {slurmNodesPerJob}",
                               "#SBATCH -p {slurmPartition}",
                               "#SBATCH -A {slurmAccount}",
                               "#SBATCH -J {slurmJobName}",
                               "#SBATCH -o {stdout_file_path}",
                               "#SBATCH -e {stderr_file_path}",
                               "#SBATCH -t {slurmTimeLimit}",
                               "#SBATCH -C {slurmMem}",
                               ""]))
        setupStr = setupTemplate.format(stdout_file_path=stdout_file_path, 
            stderr_file_path=stderr_file_path, **parsed_args_dict)
        jobsStr = "\n".join(commands)
        
        return setupStr + jobsStr
    
    def launch_commands(self, commands):
        all_commands = commands #[self.parsed_args.slurmSetupCommands] + commands
        script = self.create_sbatch_script(all_commands, self.stdio_dir, self.parsed_args)
        call_pars = shlex.split(self.parsed_args.slurmBinary) #pylint: disable=E1103
        print("launching: " + " ".join(call_pars) + " with input " + script)
        #Make the sbatch call
        (out, err) = Popen(call_pars, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate(script)
        print("launch result: " + str((out,err)))
        #assert that correct results was received
        return (out, err)

    def launch_python_function(self, f):
        main_f = create_main_function_wrapper(f)
        commands = [create_python_function_command(main_f)]
        return self.launch_commands(commands)
    

class test(unittest.TestCase):
    def test_local(self):
        res = SubprocessLauncher().launch_python_function(lambda: print("yes!"))
        print(res.get())
        
    def test_slurm(self):
        res = SlurmLauncher().launch_python_function(lambda: print("yes!"),"stdout")
        print(res)
    

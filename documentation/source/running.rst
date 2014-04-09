Running Tentacle
^^^^^^^^^^^^^^^^

The tutorials (:ref:`tutorial`) contain information and instructions
on how to prepare data for a run with Tentacle. 

Entry points
************
Tentacle has two main entry points:

 * ``tentacle_slurm.py``
 * ``tentacle_local.py``

These executables are Python scripts. They are installed into your
``%TENTACLE_VENV%/bin`` directory if Tentacle is installed using ``pip``.  If
your did not perform a ``pip`` installation they are located in
``$TENTACLE_ROOT/rundir``. You can add symlinks to them in e.g. your ``~/bin``
directory to make them universally available on your system if this is the
case.

These executables will display on-screen help in the console if run without any
arguments. The user must first choose one of the available mapping tools by
supplying the relevant command line option (e.g. ``--pblat``).  When a valid
mapper option has been supplied it is possible to display further help on all
the remaining options by supplying ``--help`` on the command line.  The options
vary a bit depending on what mapper is selected, so read them carefully. Since
options are prone to change with updates to Tentacle all of them will not be
covered here.

.. _slurm launcher:

Tentacle Slurm
**************
If Tentacle is launched using ``tentacle_slurm.py`` it will use the Slurm
resource manager to launch worker nodes. This will only work on machines/clusters
that have Slurm installed. To run Tentacle on Slurm, the following commandline
arguments are required in addition to all mapping-related arguments:

 * ``--slurmAccount`` - to specify your Slurm account name
 * ``--slurmPartition`` - to specify your Slurm partition
 * ``--slurmTimeLimit`` - time limit for nodes allocated via Tentacle

It is possible to run Tentacle with the ``--localCoordinator`` and
``--distributionUseDedicatedCoordinatorNode``. This tells Tentacle to launch
the master process on the computer from which the command is run, instead of
launching and running the master process side-by-side with computations on one
of the worker nodes. Another benefit of running Tentacle with both these commands
is that it enables a master process to continue to run even if the time for
allocated nodes should run out. 

It is possible to launch additional workers
that will attach to a currently running master process. See the next section for
information about how to create additional workers.

Create additional workers
=========================
When a master process is started, a bash shell script is created in the current
working directory (i.e. the directory from which the command was run), named 
``create_additional_workers_{JOBNAME}.sh``. This script will launch one 
additional worker node each time it is submitted to Slurm via ``sbatch``. The
script is generated when the master process is started and contains all the 
information required for a worker node to be launched and connect to the currently
running master process and start requesting jobs. Note that it is possible to 
adjust the script manually to adjust parameters like requested allocation time
in the Slurm scheduler if the time requested was too much or too little. 

The script to create additional workers is no longer required after the master
process closes and can thus be manually deleted when this has occured. 


Tentacle local
**************
If Tentacle is launched using ``tentacle_local.py`` it will launch worker nodes
locally on your computer. This can be used for trying things out or making
smaller runs that does not require a big computer cluster. Note that running
a large parallel job in local mode will put severe strain on the computer's 
I/O facilities and since most mappers are configured by default to utilize all
available CPU cores the system might become unresponsive for a while. 


Tentacle Query Jobs
*******************
There is a third script installed with the two mentioned above,
``tentacle_query_jobs.py``.  This script is a small program that makes it
possible to query a running Tentacle master process to get the status of
on-going jobs, look at (eventual) error messages from failed jobs etc. The
program contains its own help message and descriptons on how to use it. To see
instructions and help documentation, run the program with the help flag::
   
 tentacle_query_jobs.py --help

A normal invocation to get a list of currently registered jobs and their 
status could look like this (substitute for the IP address of the currently
running master process::

 tentacle_query_jobs.py tcp://127.0.0.1

It can be run for single queries (default) but also has a useful interative
mode for more continous querying of running jobs. The interactive mode is
activated with ``--interactive``. 




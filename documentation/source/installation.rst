###################
Installing Tentacle
###################
Here follows instructions on how to setup the environment required for
Tentacle.  A note on pathnames: The directory in which Tentacle is installed
will be referred to as ``$TENTACLE_ROOT`` for convenience. Also, aside from the
section on how to install, prepare, and activate virtualenv, the
``(tentacle_env)`` prefix to the command line will be omitted for brevity. Note
however, that all commands that utilize the Tentacle framework will require the
virtualenv to be activated.

Dependencies
************
Tentacle depends on a number of packages. If they are not installed they will
automatically be installed if you install Tentacle using ``pip``. Should you
decide to run Tentacle without installing it, you need to make sure that the
required packages are available in your local Python installation.  Below is a
list of the required Python packages (tested versions in parenthesis).

 * cloud (2.8.5)
 * gevent (1.0)
 * greenlet (0.4.2)
 * msgpack-python (0.4.1)
 * numpy (1.8.0)
 * psutil (1.2.1)
 * pyzmq (13.1.0)
 * zerorpc (0.4.4)


.. _virtualenv:

Python virtualenv
*****************
.. sidebar:: Python 2.7

    Since Tentacle requires Python 2.7, make sure that this is the Python version
    used when creating your virtualenv.
   
The recommended way to use Tentacle is to setup a Python virtualenv (virtual
environment), into which all required packages are installed. You can read more
about virtualenv on the official website: http://www.virtualenv.org/en/latest/.

Assuming that virtualenv is installed and globally available on your system,
create a virtual environment in which to run Tentacle::

  $ virtualenv tentacle_env

Activate the newly created (and empty) virtualenv by running the activate 
script (this will change your prompt, as illustrated below)::

  $ source tentacle_env/bin/activate
  (tentacle_env)$ 


.. _installation:

Download Tentacle sources
*************************
The Tentacle software is distributed as a downloadable compressed archive.
Either download a release tarball from the download section, or download
the latest development version from Bitbucket. It is recommended to use the
latest release version as this is probably more stable.
Example download command::

  $ wget http://bioinformatics.math.chalmers.se/tentacle/downloads/tentacle-0.1.0.tar.gz

Installing Tentacle into virtualenv
===================================
To install Tentacle into the virtualenv, make sure the virtualenv
is activated and use ``pip`` from within the virtualenv to install Tentacle::

  $ pip install tentacle-0.1.0.tar.gz

Running this command will download and install Tentacle along with all
dependencies.  Make sure all packages install correctly into the virtulenv.
Note that some of the required packages might in turn have further
dependencies.  You can verify that all packages installed correctly by running
``pip list``.

The pip installation will install the three program files
``tentacle_local.py``, ``tentacle_slurm.py``, and ``tentacle_query_jobs.py``
into the ``bin`` directory of the virtualenv. You can call these from the
command line to launch Tentacle.

Using Tentacle without installation
===================================
It is also possible (but not recommended) to run tentacle without installing it
into a virtualenv. To do this, unpack the archive and add the files in
`$TENTACLE/rundir` to your $PATH variable. This could be done for your current
user with the following commands::
  
  $ tar -xf tentacle-0.1.0.tar.gz
  $ ln -s tentacle-0.1.0/rundir/tentacle* ~/bin

Please note that this is NOT the recommended way to use Tentacle.



Sequence alignment/mapping software
***********************************
.. sidebar:: Adding support for other mappers

  Tentacle is designed to make it simple to add support for additional mapping
  tools. The section :ref:`adding mappers` contains instructions for how to
  extend the functionality of Tentacle with support for other CLI-based mappers.


To use Tentacle a sequence alignment software is required. In this documentation
they will be referred to as 'mapper' or 'sequence alignment software' interchangeably.
Tentacle comes with out-of-the-box support for the following mappers:

 * `Bowtie2`_ (2.1.0)
 * `GEM`_ (1.376 beta)
 * `pBLAT`_ (v.34)
 * `RazerS3`_ (3.2)
 * `USEARCH`_ (v7.0.1001)
 * (`NCBI BLAST`_) (2.2.28+) *[not recommended, but tested]*

.. _Bowtie2: http://bowtie-bio.sourceforge.net/bowtie2/index.shtml
.. _GEM: http://algorithms.cnag.cat/wiki/The_GEM_library
.. _pBLAT: https://code.google.com/p/pblat/
.. _RazerS3: https://www.seqan.de/projects/razers/
.. _USEARCH: http://www.drive5.com/usearch/
.. _NCBI BLAST: http://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE_TYPE=BlastDocs&DOC_TYPE=Download

For installation instructions for the alignment software, please refer to the 
respective documentation/website. 

After downloading/compiling the binaries for your mapper of interest, either 
ensure that they are available in ``$PATH`` or put the binaries (or symlinks)
in ``%TENTACLE_VENV%/bin`` so that Tentacle can find them on runtime. 


Verifying installation
**********************
This section is not yet complete. 

.. After setting up and activating the virtualenv and installing a suitable
   mapper, run one of the included tests to verify that the installation is
   working as intended. From within ``$TENTACLE_ROOT``, initiate the tests::
   
     (tentacle_env)[$TENTACLE_ROOT]$ rundir/tests_local.py
   
   This will fire off a tests for each mapper to verify that the pipeline 
   runs as intended locally on your computer. Note that these tests will 
   fail if the mappers are not installed.

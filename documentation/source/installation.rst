###################
Installing Tentacle
###################
Here follows instructions on how to setup the environment required for
Tentacle.  A note on pathnames: The directory in which Tentacle is installed
will be referred to as ``$TENTACLE_ROOT`` for convenience. Also, aside from in
the section on how to install, prepare, and activate virtualenv, the
``(tentacle_env)`` prefix to the command line will be omitted for brevity. Note
however, that all commands that utilize the Tentacle framework will require the
virtualenv to be activated.

Dependencies
************
Tentacle depends on a number of Python packages. If they are not installed they
will automatically be installed if you install Tentacle using ``pip``. Should
you decide to run Tentacle without installing it, you need to make sure that
the required packages are available in your local Python installation.  Below
is a list of the required Python packages (tested versions in parenthesis).

 * cloud (2.8.5)
 * gevent (1.0)
 * greenlet (0.4.2)
 * msgpack-python (0.4.1)
 * numpy (1.8.2)
 * psutil (1.2.1)
 * pyzmq (13.1.0)
 * zerorpc (0.4.4)

Non-Python dependencies
=======================
To run Tentacle several non-Python programs are required as well. They should
be installed and available on your ``$PATH`` or put in
``$TENTACLE_ROOT/dependencies/bin/<system>``, where ``<system>`` is either
``Linux`` or ``Darwin`` depending on if you run Linux or OS X.  The required
software is listed below (tested version in parenthesis):
 
 * ``seqtk`` (1.0-r45). Used for high-performance FASTQ to FASTA conversion.
   https://github.com/lh3/seqtk

Some software is only required if you required the functionality offered by them:

* FASTX toolkit (0.0.13): ``fastq_quality_filter``, ``fastq_quality_trimmer``. 
  http://hannonlab.cshl.edu/fastx_toolkit/

Note that a mapper (sequence alignment software) is also required. See section
`mappers`_ for information about what mappers are supported.
 


.. _virtualenv:

Python virtualenv
*****************
.. sidebar:: Python 2.7

    Since Tentacle requires Python 2.7, make sure that this is the Python
    version used when creating your virtualenv. It is possible to specify a
    Python binary for use in the created virtualenv with the ``--python``
    argument to virtualenv.  E.g. ``virtualenv --python=/usr/bin/python2.7
    tentacle_env``.
   
The recommended way to use Tentacle is to setup a Python virtualenv (virtual
environment), into which all required packages are installed. You can read more
about virtualenv on their `official website
<https://virtualenv.pypa.io/en/latest/>`_.

To install virtualenv on your local computer cluster might require
administrator privileges, contact your server adminstrator or support if it is
not already available on your system.

Assuming that virtualenv is installed and globally available on your system,
create a virtual environment in which to run Tentacle::

  $ virtualenv tentacle_env

Activate the newly created (and empty) virtualenv by running the activate
script (this will change your prompt to show that the environment has been
activated, as illustrated below)::

  $ source tentacle_env/bin/activate
  (tentacle_env)$ 


.. _installation:

Download and install Tentacle 
*****************************

.. _Mercurial: https://mercurial.selenic.com/
.. _Bitbucket: https://bitbucket.org/chalmersmathbioinformatics/tentacle

The Tentacle programs and framework is distributed via its Bitbucket_
repository. This requires that the distributed version control system
Mercurial_ is installed. The most recent version can be automatically
downloaded and installed directly from the online repository with the following
command::

   (tentacle_env)$  pip install -e hg+http://bitbucket.org/chalmersmathbioinformatics/tentacle/#egg=Tentacle

Running this command will install Tentacle along with all dependencies (it will
download any required dependencies that might be missing). Take a look at the
output to make sure all packages install correctly into the virtulenv. Note
that some of the required packages might in turn have further dependencies,
these will install automatically. You can verify that all packages installed
correctly by running ``pip list`` to see a listing of all packages that are
installed in your virtualenv.

The pip installation will automatically make links to the three program files
``tentacle_local.py``, ``tentacle_slurm.py``, and ``tentacle_query_jobs.py``
into the ``bin`` directory of the virtualenv. You can call these from the
command line to launch Tentacle from any folder.


Download and installing Tentacle manually
*****************************************
If Mercurial_ is unavailable or you require to install Tentacle without
downloading it from the Bitbucket_ repository, Tentacle can also be installed
from a downloaded compressed archive. However, to get the most recent version
we recommend installing it directly from the Bitbucket_ repository. If you are
unable to install Tentacle from the repository directly, you can install it
using a release tarball as described in :ref:`download`.

The Tentacle programs and framework is distributed via its `Bitbucket
repository`_ repository. This requires that the distributed version control
system `Mercurial`_ is installed. The most recent version can be automatically
downloaded and installed directly from the online repository with the following
command::

  (tentacle_env)$  pip install -e hg+http://bitbucket.org/chalmersmathbioinformatics/tentacle/#egg=Tentacle

Running this command will install Tentacle along with all dependencies (it will
download any required dependencies that might be missing). Take a look at the
output to make sure all packages install correctly into the virtulenv. Note
that some of the required packages might in turn have further dependencies,
these will install automatically.  You can verify that all packages installed
correctly by running ``pip list`` to see a listing of all packages that are
installed in your virtualenv.

The pip installation will automatically make links to the three program files
``tentacle_local.py``, ``tentacle_slurm.py``, and ``tentacle_query_jobs.py``
into the ``bin`` directory of the virtualenv. You can call these from the
command line to launch Tentacle from any folder.

Downloading and installing Tentacle manually
============================================
If `Mercurial`_ is unavailable or you require to install Tentacle without
downloading it from the `Bitbucket repository`_, Tentacle can also be installed
from a downloaded compressed archive. However, to get the most recent version
we recommend installing it directly from the `Bitbucket repository`_.  If you
are unable to installed Tentacle from the repository directly, you can install
it using a release tarball as described in :ref:`download`.

To install Tentacle from a downloaded compressed archive into the virtualenv,
make sure the virtualenv is activated and use ``pip`` from within the
virtualenv to install Tentacle::

  (tentacle_env)$ pip install tentacle-0.1.0b.tar.gz

You can also install Tentacle from a downloaded clone of the `Bitbucket
repository`_.  Assuming that the repository has been cloned to a folder
``./tentacle`` in your current directory, you can install it using ``pip`` like
by issuing this command::

  (tentacle_env)$ pip install ./tentacle

Using Tentacle without installation
===================================
It is also possible (but not recommended) to run tentacle without installing it
into a virtualenv. To do this, unpack the archive and add the files in
``$TENTACLE/rundir`` to your ``$PATH`` variable. This could be done for your
current user with the following commands::
  
  $ tar -xf tentacle-0.1.0.tar.gz
  $ ln -s tentacle-0.1.0/rundir/tentacle* ~/bin

This should work with a fresh clone of the `Bitbucket repository`_ as well. But
please note that this is NOT the recommended way to use Tentacle.

.. _mappers:

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
 * (`NCBI BLAST`_) (2.2.28+) *[not recommended: very slow]*

.. _Bowtie2: http://bowtie-bio.sourceforge.net/bowtie2/index.shtml
.. _GEM: http://algorithms.cnag.cat/wiki/The_GEM_library
.. _pBLAT: http://icebert.github.io/pblat/
.. _RazerS3: https://www.seqan.de/projects/razers/
.. _USEARCH: http://www.drive5.com/usearch/
.. _NCBI BLAST: http://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE_TYPE=BlastDocs&DOC_TYPE=Download

For installation instructions for the alignment software, please refer to the 
respective documentation/website. 

After downloading/compiling the binaries for your mapper of interest, either 
ensure that they are available in ``$PATH`` or put the binaries (or symlinks)
in ``%TENTACLE_VENV%/bin`` so that Tentacle can find them on runtime. 


.. Verifying installation
.. **********************
.. This section is not yet complete. 

.. After setting up and activating the virtualenv and installing a suitable
   mapper, run one of the included tests to verify that the installation is
   working as intended. From within ``$TENTACLE_ROOT``, initiate the tests::
   
     (tentacle_env)[$TENTACLE_ROOT]$ rundir/tests_local.py
   
   This will fire off a tests for each mapper to verify that the pipeline 
   runs as intended locally on your computer. Note that these tests will 
   fail if the mappers are not installed.

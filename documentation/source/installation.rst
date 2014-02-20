#########################
Installation instructions
#########################
Here follows instructions on how to setup the environment required for Tentacle.

Dependencies
************
Tentacle depends on a number of packages, all of which are easily installed
e.g. using `pip`. Below are the required Python packages (tested versions
in parenthesis).

 * cloud (2.8.5)
 * Cython (0.19.2)
 * gevent (1.0)
 * greenlet (0.4.1)
 * msgpack-python (0.4.0)
 * numpy (1.8.0)
 * psutil (1.2.1)
 * pyzmq (13.1.0)
 * zerorpc (0.4.4)


.. _virtualenv:

Python virtualenv
*****************
The recommended way to use Tentacle is to setup a Python virtualenv (virtual 
environment), in which all required packages are installed. Assuming that 
virtualenv is installed and globally available on your system, create a 
virtual environment in which to run Tentacle::

  $ virtualenv tentacle_env

Activate the newly created (and empty) virtualenv by running the activate 
script (this will change your prompt, as illustrated below)::

  $ source tentacle_env/bin/activate
  (tentacle_env)$ 

To install the required packages into the virtualenv, make sure the virtualenv
is activated, then use `pip` from the virtualenv to install the packages::

  (tentacle_env)$ pip install cython
  (tentacle_env)$ pip install greenlet
  (tentacle_env)$ pip install gevent
  (tentacle_env)$ pip install pyzmq
  (tentacle_env)$ pip install cloud
  (tentacle_env)$ pip install numpy
  (tentacle_env)$ pip install msgpack-python
  (tentacle_env)$ pip install zerorpc
  (tentacle_env)$ pip install psutil

Make sure all packages install correctly into the virtulenv. Note that some
of the listed packages might in turn have further dependencies. 

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
ensure that they are available in `$PATH` or put the binaries (or symlinks)
in `$TENTACLE_ROOT/dependencies/bin/Linux` so that Tentacle can find them 
on runtime. 



Verifying installation
**********************
After setting up and activating the virtualenv and installing a suitable
mapper, run one of the included tests to verify that the installation is
working as intended. From within `$TENTACLE_ROOT`, initiate the tests::

  (tentacle_env)[$TENTACLE_ROOT]$ rundir/tests_local.py

This will fire off a tests for each mapper to verify that the pipeline 
runs as intended locally on your computer. Note that these tests will 
fail if the mappers are not installed.

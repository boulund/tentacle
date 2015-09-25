.. _download:

########
Download
########

Download Tentacle
*****************
There are several ways to acquire Tentacle. The easiest is to just download
and install Tentacle directly from the `Bitbucket repository`_::

  (tentacle_env)$  pip install -e hg+http://bitbucket.org/chalmersmathbioinformatics/tentacle/#egg=Tentacle

This process is further described in :ref:`installation`. If this
for some reason does not work for you, another possibility is to download a
release tarball from our servers and install it using ``pip``::

  (tentacle_env)$  wget http://bioinformatics.math.chalmers.se/tentacle/download/tentacle-0.1.0b.tar.gz
  (tentacle_env)$  pip install tentacle-0.1.0b.tar.gz

The third option is to download it directly from the `Bitbucket
repository`_ using your browser of choice.

.. _Bitbucket repository: https://bitbucket.org/chalmersmathbioinformatics/tentacle

As a last resort if everything else fails, the entire `Bitbucket repository`_ can be
cloned and used to install Tentacle without downloading a compressed archive. Clone the
repository using Mercurial (``hg``) like this::

  hg clone http://hg@bitbucket.org/chalmersmathbioinformatics/tentacle tentacle

You can then follow the instructions in :ref:`installation` to install Tentacle
from the repository clone.


Tutorial data
*************
To follow the tutorial you need the data referred to by the tutorial instructions.
It can be downloaded from here:

  http://bioinformatics.math.chalmers.se/tentacle/download/tentacle_tutorial.tar.gz

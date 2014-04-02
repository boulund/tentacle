#!/usr/bin/env python
# coding: utf-8
# Date: 2014-04-01
# Author: Fredrik Boulund
from setuptools import setup, find_packages

setup(name="tentacle",
      version="0.1.0",
      description="Gene mapping/quantification distribution framework",
      author="Fredrik Boulund",
      author_email="fredrik.boulund@chalmers.se",
      maintainer="Fredrik Boulund",
      maintainer_email="fredrik.boulund@chalmers.se",
      url="http://bioinformatics.math.chalmers.se/tentacle/",
      download_url="https://bitbucket.org/chalmersmathbioinformatics/tentacle",
      install_requires=['cloud', 
                'gevent>=1',
                'greenlet', 
                'msgpack-python', 
                'numpy', 
                'psutil', 
                'pyzmq', 
                'zerorpc'
               ],
      packages=find_packages(),
      package_data={'tentacle': ['README.rst'],
                   },
      data_files=[('bin', ['dependencies/bin/Linux/fastq_quality_filter', # TODO: Add OS detection
                                              'dependencies/bin/Linux/fastq_quality_trimmer',
                                              'dependencies/bin/Linux/seqtk',
                                              'dependencies/bin/Linux/pblat',
                                              'dependencies/bin/Linux/razers3'])
                 ],
      scripts=['rundir/tentacle_local.py', 
               'rundir/tentacle_slurm.py', 
               'rundir/tentacle_query_server.py'
              ],
      classifiers=['Programming Language :: Python :: 2.7',
                   'Intended Audience :: Science/Research',
                   'Development Status :: 4 - Beta',
                   'Operating System :: POSIX :: Linux',
                   'Operating System :: MacOS',
                   'Topic :: Scientific/Engineering :: Bio-Informatics',
                  ],
     )

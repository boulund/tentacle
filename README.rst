========
Tentacle
========

:Authors: Fredrik Boulund, Anders Sjögren, Erik Kristiansson
:Contact: fredrik.boulund@chalmers.se
:License: GPL

Welcome! This is the README for the distributed gene quantification
framework Tentacle.

Tentacle lets you compute coverage on very large metagenomic data sets using distributed computing resoources controlled by e.g. Slurm. 
Mapping can be performed using a range of popular mappers, including Bowtie 2, USEARCH, BLAT, and BLAST.

The complete documentation for Tentacle is available online at 
http://bioinformatics.math.chalmers.se/tentacle/.

Citing Tentacle
***************
If you use Tentacle in your research, please cite us!.

The work is described in Boulund et al. (2015). Tentacle: distributed gene quantification in metagenomes. *GigaScience* 2015, **4**:40.

DOI: 10.1186/s13742-015-0078-1.


Installing Tentacle
*******************
Tentacle can be easily installed using ``pip``:

``pip install -e hg+http://bitbucket.org/chalmersmathbioinformatics/tentacle/#egg=Tentacle``

Complete installation instructions with additional details are available in the manual provided online at
http://bioinformatics.math.chalmers.se/tentacle/
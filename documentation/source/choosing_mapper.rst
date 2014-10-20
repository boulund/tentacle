.. _Choosing mapper:

Choosing mapper
^^^^^^^^^^^^^^^

Bowtie2
*******
Bowtie2 is a widely used mapping tool that is well suited for mapping reads to
reasonably large databases and is commonly used for mapping to the human
genome. As Bowtie2 requires a pre-constructed index its use in Tentacle is best
suited when comparing to a single large database of reference sequences. It is
implemented in Tentacle mainly as a reliable tool to perform filtering of human
reads from metagenomic samples. Our testing showed that Bowtie2 was unable to
handle a case with a very large reference database (7.5 GiB in FASTA format).
Bowtie2 is parallelized to take advantage of several CPUs. 

GEM
***
GEM has implemented a mapping algorithm that also requires the construction of
a pre-computed index. GEM was the only software in our testing that was capable
of handling our largest test database weighing in at 7.5 GiB containing 11.5
million sequences in FASTA format. The GEM paper explains that GEM
provides "fully tunable exhaustive searches that return all existing matches,
including gapped ones". GEM is parallelized and can take advantage of several
CPUs.

BLAT
****
pBLAT is a parallelized version of the widely used BLAT tool. The
parallelization allows pBLAT to utilize several CPUs on a single computer in a
way that the original BLAT tool is unable to. The pBLAT website states "It can
reduce run time linearly, and use almost equal memory as the original blat
program". As pBLAT does not require a precomputed index it is well suited for
e.g. mapping metagenomic samples to their assembled contings, which otherwise
would require preparing many separate indexes if mapping with other mappers.

RazerS 3
********
RazerS 3 is a mapper that implements an algorithm that is well suited for
aligning long reads with high error rates. RazerS 3 does not require a
precomputed index, thus making it applicable in cases where metagenomic samples
are mapped to their assembled contigs, just like e.g. pBLAT. The RazerS 3
publication shows that RazerS 3 often displays superior sensitivity when
compared to other mappers. RazerS 3 is parallelised and can utilize several
CPUs.

USEARCH
*******
USEARCH is a widely used sequence alignment software that implements many
BLAST-like sequence alignment options with a significantly higher speed and
comparable sensitivity. The algorithm can create database indexes on-the-fly
but can also precompute indexes to save time in cases where the same reference
is used for all samples. USEARCH can utilize several CPUs and is capable of
performing translated searches (e.g. searching with nucleotide reads against a
protein database), making it very useful for quantifying the presence of
specific genes in a metagenomic dataset.

BLAST
*****
NCBI BLAST is a ubiquitous alignment algorithm that requires little
introduction and capable of many different types of queries. It is not
parallelized (however, as previously mentioned, some parallelized
implementations such as mpiBLAST do exist). A mapping module for BLAST
is included in Tentacle because it is widely used and the existence of such a
module enables researchers that already use BLAST in their workflows to try out
Tentacle without modifying too much of the workflow. However, we strongly
discourage the use of BLAST because of its relatively slow speed compared to
the previously described algorithms that can be hundreds of times faster than
BLAST. Tentacle allows users that require the use of BLAST to essentially
reduce the computation time by a factor of N, where N is the number of nodes
used (as seen in the scaling evaluation).


.. _Quantification accuracy:

Quantification accuracy
^^^^^^^^^^^^^^^^^^^^^^^
We investigated the quantification accuracy of our framework by constructing a
small synthetic metagenome where all abundances are known beforehand.  The
accuracy of quantification depends highly on how abundance of a reference gene
is defined, but also what mapper and what settings are used when aligning
sequences.  In our investigations of quantification accuracy we have decided
that the abundance of a gene is the number of reads that originate from a
specific reference sequence and should map to the gene in question (note that
this means our definition thus does not require complete coverage of the gene).

To test this, we created a synthetic metagenomic data set where random
fragments were created from a set of reference sequences, in addition to
several completely random fragments created without the reference sequences as
template.  Some reads drawn from the reference sequences were randomly
“mutated” by introduction single point mutations at a rate of approximately 5%.
The mapping program used in this evaluation was RazerS3 (settings: ``-I 95 –rr
100 –m 1 –tc 32`` ) and the quantification results show that all reads that
were drawn from the reference sequences (and thus should map back to the
reference sequences) did map to the correct reference sequence. 

########
Tutorial
########

This part of the documentation shows examples of how to apply Tentacle
to quantifying the contents of metagenomic samples. The sections below
showcase how to best utilize Tentacle in different mapping scenarios, 
depending on the biological question.

The tutorials showcased here come with prepared example files that are
available for download in section :ref:`download`. Note that the tutorial
file contains example files for all tutorial examples showcased below, 
to provide a complete tutorial experience.


Important information about files and file formats
**************************************************
The Tentacle pipeline requires three types of input files:

 * Reads (query sequences)
 * Reference sequences
 * Annotation for the reference sequences

Reads
=====
Reads (or query sequences) are normally metagenomic reads produced with
high-throughput sequencing technologies such as Illumina. The reads
can be supplied to Tentacle as either FASTQ (with quality scores) or
FASTA files. The Tentacle pipeline can figure out what to do with either,
but be aware that quality filtering cannot be performed and will be skipped
for input files in FASTA format (it lacks quality information).

It is important to note that the input read files should preferrably be
located on a parallel file system that has high throughput and can handle
the high load that will be put on it when Tentacle is running.

References
==========
Reference sequences are normally some kind of annotated reference
sequences. Tentacle expects reference sequences to be available in FASTA
format, as this is the format used when indexing the reference sequences
for coverage calculations. 

Certain mappers require that the reference sequences are available in
a custom database format (e.g. USEARCH uses .udb and bowtie2 has several
indexes in .bt2.* files). It is important to note that you prepare 
the reference sequences (FASTA file + potential database-related files)
so that they share the same **basename** (i.e. the filename up until
the first dot "."). For example, in the USEARCH case, create a tarball
containing the following files::

  references.fasta
  references.udb

It does not matter what you call the tarball, as long as the basename for
the FASTA file and the database-related files are the same. 


Annotations
===========
The annotations are used in Tentacle when producing the coverage output. 
Tentacle computes the coverage (i.e. how large portions of the reference
sequences that have reads aligned to them) and requires the annotation of
the reference sequences to produce that output. 

The annotation file is a simple tab separated text file with one annotated
region per line. The format of the annotation file is as follows::

  reference_name      start   end    strand     annotation
  [ascii; no space]   [int]   [int]  [+ or -]   [ascii; no space]

The first few lines of an example annotation file could read::

  scaffold3_2_MH0014  899 3862    +   COG3321
  scaffold6_1_MH0014  1   570     +   COG0768
  scaffold11_2_MH0014 3   1589    -   NOG08628
  scaffold13_1_MH0014 3   260     -   NOG21937
  scaffold13_1_MH0014 880 1035    +   COG0110

As you can see in the example above, a reference sequence can occur on multiple
lines, with different annotations on each line. 

**The annotation file is required in order to compute the coverage of each
annotated region of the reference sequences. Tentacle will not start 
without an annotation file**

There is a special case where the entire length of each reference sequence
is the actual annotated region (e.g. when the reference file contains
entire genes). In such cases it is easy to create a dummy annotation
file that annotates the entire length of each sequence in the reference
FASTA file. Just put a + in the strand column.




TUTORIAL 1. Mapping reads to contigs (pBLAT)
*********************************************
This mapping scenario is relevant for quantifying the gene content 
of a complete metagenome. 

Step-by-step tutorial
=====================
To begin this tutorial, extract the tutorial tarball, available from :ref:`download`.
It contains a folder called tutorial_1 which contains the following files that 
are relevant for this part of the tutorial::

  tutorial_1/
  tutorial_1/data/annotation_1.tab      tab-delimited file with annotation for references.fasta
  tutorial_1/data/annotation_2.tab      tab-delimited file with annotation for references.fasta
  tutorial_1/data/reads_1.fasta         reads in FASTA format
  tutorial_1/data/reads_2.fasta         reads in FASTA format
  tutorial_1/data/contigs_1.fasta       contigs in FASTA format
  tutorial_1/data/contigs_2.fasta       contigs in FASTA format
  tutorial_1/mapping_manifest.tab       tab-delimited listing of what read files should be mapped to what references
  tutorial_1/map_with_pblat.py          the 'program'


Step 1: Setting up the mapping manifest
---------------------------------------


Step 2: Deciding on settings
----------------------------


Step 3: Run Tentacle
--------------------


Step 4: Check results 
---------------------



TUTORIAL 2. Mapping nucleotide reads to amino acid database (USEARCH)
***********************************************************************
This mapping scenario is common typically when a reference database (ref DB) 
of known genes exists (e.g. known antibiotic resistance genes). Since
all metagenomic samples needs to be compared to the same reference genes, a
single ref DB is constructed beforehand. This steps displayed in this tutorial
are relevant for other mappers using a premade ref DB such as Bowtie2, GEM,
BLAST etc.

Introductory remarks
=====================

.. sidebar:: Modification of mapper call

   How the actual commandline is constructed in Tentacle is defined in the 
   mapping module usearch.py; the interested reader should have a look there to
   see how it is constructed. 

In this example we will use USEARCH as the mapper because of its excellent 
performance in the nucleotide-to-amino-acid mapping scenario (translated search). 
As we are only interested in identifying the best matches we will utilize 
the *usearch_global* algorithm and search both strands of the reads. 
We are interested in genes with high sequence identity to the references 
and will only pick the best hit. 
If we boil it down to what we would run on a single machine, the commandline 
might look like this::

  $ usearch -usearch_global reads.fasta -db references.udb -id 0.9 -strand both

Step-by-step tutorial
=====================
To begin this tutorial, extract the tutorial tarball, available from :ref:`download`.
It contains a folder called tutorial_2 which contains the following files that 
are relevant for this part of the tutorial::

  tutorial_2/
  tutorial_2/data/annotation.tab        tab-delimited file with annotation for references.fasta
  tutorial_2/data/reads_1.fasta         reads in FASTA format
  tutorial_2/data/reads_2.fasta         reads in FASTA format
  tutorial_2/data/references.fasta      references in FASTA format
  tutorial_2/mapping_manifest.tab       tab-delimited listing of what read files should be mapped to what references
  tutorial_2/map_with_usearch.py        the 'program'


Step 1: Preparing the ref DB
----------------------------
Before any mapping can take place, we need to 


Step 2: Setting up the mapping manifest
---------------------------------------


Step 3: Deciding on settings
----------------------------


Step 4: Run Tentacle
--------------------


Step 5: Check results 
---------------------






Other mapping scenarios
***********************
Different mappers are best suited for different mapping tasks. With
Tentacle it is possible to select the mapper that works best for your
specific mapping scenario. The table below lists some scenarios and examples 
of what mappers might be best suited.

============================    =====================   =============================================
Scenario                        Mapper(s)               Comments
============================    =====================   =============================================
Reads to annotated contigs      pBLAT, RazerS3          Many small "references" files, potentially 
                                                        different for each reads file.
                                                        No precomputed reference DB.
Reads to nt reference           USEARCH, GEM, Bowtie2   GEM works well with very large reference DBs
Reads to aa reference           USEARCH                 BLASTX-like scenario, *translated search*
============================    =====================   =============================================


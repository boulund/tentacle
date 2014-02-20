########
Tutorial
########

This part of the documentation shows examples of how to apply Tentacle
to quantifying the contents of metagenomic samples. The sections below
showcase how Tentacle can be used in different mapping scenarios, 
depending on the biological question.

The tutorials showcased here come with prepared example files that are
available for download in section :ref:`download`. Note that the tutorial
file contains example files for all tutorial examples showcased below, 
to provide a complete tutorial experience.


Important information about files and file formats
**************************************************
The Tentacle pipeline requires three types of data files:

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
Reference sequences are normally some kind of gene or predicted ORF data.
Tentacle expects reference sequences to be available in FASTA
format, as this is the format used when indexing the reference sequences
for coverage calculations. 

Certain mappers require that the reference sequences are available in
a custom database format (e.g. USEARCH uses `*.udb` and bowtie2 has several
indexes in `*.bt2.*` files). It is important to note that you must prepare 
the reference sequences (FASTA file + potential database-related files)
so that they share the same **basename** (i.e. the filename up until
the first dot "."). For example, in the USEARCH case, create a tarball
containing the following files::

  $ ls
  references.fasta references.udb
  $ tar -zvcf reference_tarball.tar.gz references.fasta references.udb


It does not matter what you call the tarball, as long as the basename for
the FASTA file and the database-related files are the same (in the above
example the basename is *references*). 
The basename is important to remember to add to the command line arguments 
when running Tentacle so that the mapper can find the correct files later,
e.g. for USEARCH the command line flag is `--usearchDBName`. Refer to the
command line help for each mapper for their specific flag name.


Annotations
===========
The annotations are used in Tentacle when producing and computing the 
coverage output. Tentacle computes the coverage (i.e. how large 
portions of the reference sequences that have reads aligned to them) 
and requires the annotation of the reference sequences to produce 
that output. 

The annotation file is a simple tab separated text file with one annotated
region per line. The format of the annotation file is as follows::

  reference_name      start   end    strand     annotation
  [ascii; no space]   [int]   [int]  [+ or -]   [ascii; no space]

The first few lines of an example annotation file could read::

  scaffold3_2    899 3862    +   COG3321
  scaffold6_1    1   570     +   COG0768
  scaffold11_2   3   1589    -   NOG08628
  scaffold13_1   3   260     -   NOG21937
  scaffold13_1   880 1035    +   COG0110

As you can see in the example above, a reference sequence can occur on multiple
lines, with different annotations on each line. 

**The annotation file is required in order to compute the coverage of each
annotated region of the reference sequences. Tentacle will not run 
without an annotation file.**

There is a special case where the entire length of each reference sequence
is the actual annotated region (e.g. when the reference file contains
entire genes). In such cases it is easy to create a dummy annotation
file that annotates the entire length of each sequence in the reference
FASTA file. Just put a + in the strand column.




TUTORIAL 1. Mapping reads to contigs (pBLAT)
*********************************************
This mapping scenario is relevant for quantifying the gene content 
of a complete metagenome. In this tutorial the mapper `pBLAT` will
be used. However, the techniques displayed in this tutorial applies
equally to other mappers that do not require a premade database
(i.e. that can map a FASTA/FASTQ reads file to a FASTA reference), 
such as for example RazerS3.

Step-by-step tutorial
=====================
To begin this tutorial, extract the tutorial tarball, available from :ref:`download`.
It contains a folder called `tutorial_1` which contains the following files that 
are relevant for this part of the tutorial::

  tutorial_1/
  tutorial_1/data/annotation_1.tab      tab-delimited file with annotation for references.fasta
  tutorial_1/data/annotation_2.tab      tab-delimited file with annotation for references.fasta
  tutorial_1/data/reads_1.fasta         reads in FASTA format
  tutorial_1/data/reads_2.fastq         reads in FASTQ format
  tutorial_1/data/contigs_1.fasta       contigs in FASTA format
  tutorial_1/data/contigs_2.fasta       contigs in FASTA format
  tutorial_1/map_with_pblat.py          the 'program'

In our example, we are mapping reads from two small sequencing projects
back to the contigs that were assembled from the same reads. One of the
input read files is in FASTQ format, and one is in FASTA. 


Step 1: Setting up the mapping manifest
---------------------------------------
For Tentacle to know what to do, a *mapping manifest* must be created.
The manifest details what reads file should be mapped to what reference
using what annotation. By utilizing a mapping manifest file, it is 
easy to go back to old runs and inspect their mapping manifests. 

The format for the mapping manifest is simple; it consists of three
columns with absolute paths for the different files in the following
order::

  {reads}   {reference}   {annotation}

To create a mapping manifest is easy. The simplest way is probably to
use the standard GNU tools `find` and `paste`. Assuming you are
standing in the `tutorial_1` directory it could look like this::

  $ find `pwd`/data/r* > tmp_reads
  $ find `pwd`/data/c* > tmp_references
  $ find `pwd`/data/a* > tmp_annotations
  $ paste tmp_reads tmp_references tmp_annotations > mapping_manifest.tab
  $ rm tmp_*

What happens is that `find` lists all files matching the pattern `r*` in the
data directory under our current working directory (`pwd` returns the 
absolute path to the current working directory), i.e. all read files
in the data directory. We then do the same for the references (contigs
in this case) and the annotation files. After we have produced three files
containing listings of the absolute paths of all our data files, we paste
them together using `paste` into a tab separated file `mapping_manifest.tab`.
This technique can easily be extend to add files from different folders
by appending (`>>`) to the `tmp_reads` for example. 

There is no need to follow this specific procedure for the creation of 
the mapping manifest; you are free to use whatever tools or techniques
you want for the mapping manifest as long as the end result is the same.
It must contain absolute paths to all files and each row should contain
three entries with read, reference, and annotation file. 


Step 2: Deciding on settings
----------------------------
As `pBLAT` is only able to read FASTA format files, the reads file in
FASTQ format needs to be converted. Tentacle does this automatically 
when it detects that we are using a mapper that does not accept FASTQ
input. The user does not have to do anything here.

For this tutorial we will use the default settings that `pBLAT` uses
for mapping. For a list of options that can be modified for this 
specific mapper, run Tentacle with the `--pblat --help` command line 
options.  


Step 3: Run Tentacle
--------------------
First of all, make sure that the Python virtualenv that we created in
the :ref:`virtualenv` section is activated. 
Tentacle can be run on the commandline by calling the file `tentacle_parallel.py`
in `$TENTACLE/rundir`. 


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
  tutorial_2/data/reads_2.fastq         reads in FASTQ format
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


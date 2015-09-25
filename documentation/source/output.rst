.. _output:

Tentacle output
^^^^^^^^^^^^^^^

The output from Tentacle is written to the output directory, which can be
specified with ``--outputDirectory``. The default output directory is called
``tentacle_output`` and will, after a finished run, contain two folders and one
file::

 [tentacle_output]$ ls
 logs results run_summary.txt

The folder ``logs`` contains all the log files produced during the run, ready
for inspection if something went wrong. The ``results`` folder will contain one
file with results for each reads file (mapping job) in the run. The last file,
``run_summary.txt``, contains an overview of all the jobs in the run.

Tentacle output format
**********************
The format of the output file that Tentacle produces is a tab separated text
file with five fields: annotation, number of mapped reads, median number of
mapped reads, mean number of mapped reads, standard deviation of mapped reads.
The format is as follows (with TAB as separating character)::

  contig_annotation:startpos:endpos:strand  count  median   mean     stdev
  [contig: string (no tabs or spaces)    ]  [int]  [float]  [float]  [float]
  [annotation: string (to tabs or spaces)]
  [startpos: int                         ]
  [endpos : int                          ]
  [strand: + or -                        ]

  
This format is easy to parse and make further analyses on. Since each
reference sequence header (e.g. ``scaffold3_2``) is separated with a ``_``
before the annotation name (e.g. ``COGxxxxx``) it is easy to separate the
annotation name from the reference sequence header and extract further
information like start and stop coordinates of the annotation. Statistics like
number of mapped reads (count), median, mean, and standard deviation, of mapped
reads to each annotated region of the reference are useful when making further
analyses of the data.

An example of Tentacle output could look like this (with TABs instad of
spaces)::

  scaffold3_2_COG3321:898:3862:+   9   9.0 9.0 0.0
  scaffold6_1_COG0112:0:570:+   1   1.0 1.0 0.0
  scaffold11_2_NOG08628:2:1589:-   8   8.0 8.0 0.0
  scaffold13_1_COG0028:2:260:-  0   0.0 0.0 0.0

In this simple example the first COG3321 annotated region on scaffold3_2 has
had 9 reads that mapped to it, for a median, mean and standard deviation of
9.0, 9.0, and 0.0, respectively. 

.. _coverage:

########
Coverage
########

Coverage is computed for annotated regions in the reference database and
implemented as follows. Each sequence in the reference database is represented
by an array of integers which are incremented and decremented by 1 for each
alignment start and end position respectively. Coverage over each reference
sequence is then calculated as the cumulative sum over the corresponding array.
The calculation of coverage has a time complexity of O(n + N), where
nis the total number of bases in the reference database and N is the
number of mapped reads. This is substantially faster than the naïve
approach which for each mapped read increments the coverage for each mapped
base, yielding a time complexity of O(n + N*M), where M is the
maximum number of bases per read. 

Modifying how coverage is computed
**********************************
The Tentacle modules that compute coverage are located in
``tentacle/coverage``.  They use the mapping data in the ``contigCoverage``
data structure that is populated in ``tentacle/parsers/index_references.py``.
Check the code in that file to see how the dictionary is laid out. Essentially
the dicionary holds a NumPy array for each of the sequences in the reference
file. The array contains integers and after going through the mapper output
each position in the array contains a number representing the number of times
that position was covered by a read. 

It is possible to modify the way the statistics are computed. See the files in 
the ``coverage`` module to see how it works.

Functions in the coverage module
********************************

Coverage
========
This module contains all the functions required to manipulate the contig
coverage data structure. 

.. automodule:: tentacle.coverage.coverage
    :members:
    :undoc-members:
    :show-inheritance:

Statistics
===========
This module contains the function that computes statistics across annotated
regions of the reference sequences. 

.. automodule:: tentacle.coverage.statistics
    :members:
    :undoc-members:
    :show-inheritance:


Compute and write coverage statistics
=====================================
This module contains a single function responsible for formatting the output.

.. automodule:: tentacle.coverage.compute_and_write_coverage_statistics
    :members:
    :undoc-members:
    :show-inheritance:

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

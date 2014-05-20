"""Tentacle coverage module.

.. moduleauthor:: Fredrik Boulund <fredrik.boulund@chalmers.se>

date:: 2014-04-30

"""
import numpy as np

def compute_region_statistics(region):
    """
    Compute general statistics of reads mapped to a region of a contig.

    Input:
        region  a NumPy array of ints with the number of reads mapped
                to the region.
    Output:
        median  (float) the median number of reads mapped to the region.
        mean    (float) the mean numbr of reads mapped to the region.
        stdev   (float) the standard deviation of number of reads
                mapped to the region.
    """
    return (np.median(region), np.mean(region), np.std(region))


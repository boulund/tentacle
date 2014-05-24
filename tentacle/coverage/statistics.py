"""Tentacle coverage module.

.. moduleauthor:: Fredrik Boulund <fredrik.boulund@chalmers.se>

date:: 2014-04-30

"""
#  Copyright (C) 2014  Fredrik Boulund and Anders Sjögren
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
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


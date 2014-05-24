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
"""Tentacle parse mapping output and compute coverage/counts.

author:: Fredrik Boulund
date:: 2014-05-07<F5>
purpose:: Parses mapping output in different formats and extracts mapped read information
          used in coverage/counts computations..
          
"""
import numpy as np
import blast8
import razers3
import sam
import gem

def parse_mapping_output(mapper, mappings, contig_data, options, logger):
    """
    Adds the number of mapped reads to the correct positions in 
    a contig_data dictionary.

    Uses NumPy.

    Input:
        mapper      mapper object used to map the data
        mappings    mapper output file.
        contig_data  the contig_data dictionary
        options     all options
        logger      a logger object
    Output:
        contig_data 
    """
    contig_data = mapper.output_parser(mappings, contig_data, options, logger)

    if not options.noCoverage:
        for contig in contig_data.keys():
            np.cumsum(contig_data[contig]["__coverage__"], dtype=np.int32, out=contig_data[contig]["__coverage__"])
    return contig_data

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
"""Tentacle parsers blast tabular output

author:: Fredrik Boulund
date:: 2014-04-30
"""

import numpy as np
from ..coverage import update_contig_data

def parse_blast8(mappings, contig_data, options, logger):
    """ Parses mapped data in blast8 format (e.g. for usearch, pblat, blast).  """
    #DEBUG
    #np.set_printoptions(threshold='nan') 

    def check_new_read(contig_data, read, identity, aligned_length, contig, sstart, send, previous_read, previous_information):
        """ Determines if the most recently parsed read has been seen before """
        # We cannot assume the output is ordered so 
        # check if readname has already been seen and 
        # determine if the new hit is better before 
        # committing to contig_data.
        if read in previous_readname:
            logger.debug("Read {} seen before".format(read))
            if identity > previous_information[0]:
                logger.debug("Read {}          with stats {}, {}, {}, {}, {},  is better than previous".format(read, identity, mismatches, contig, sstart, send))
                logger.debug("Read {} with stats {}, {}, {}, {}, {}".format(previous_readname, previous_information[0], previous_information[1], previous_information[2], previous_information[3], previous_information[4]))
                previous_information = (identity, aligned_length, contig, sstart, send)
            elif identity == previous_information[0]:
                if aligned_length > previous_information[1]:
                    logger.debug("Read {}          with stats {}, {}, {}, {}, {},  is better than previous".format(read, identity, mismatches, contig, sstart, send))
                    logger.debug("Read {} with stats {}, {}, {}, {}, {}".format(previous_readname, previous_information[0], previous_information[1], previous_information[2], previous_information[3], previous_information[4]))
                    previous_information = (identity, aligned_length, contig, sstart, send)
        else:
            logger.debug("Read {} NOT seen before".format(read))
            if previous_information:
                logger.debug("Read {} with stats {}, {}, {}, {}, {}, was best hit, committing to contig_data".format(
                                previous_readname, previous_information[0], previous_information[1], previous_information[2], previous_information[3], previous_information[4]))
                _, _, contig, sstart, send = previous_information
                contig_data = update_contig_data(contig_data, contig, sstart-1, send, options, logger)
            previous_readname.clear()
            previous_readname.add(read)
            previous_information = (identity, aligned_length, contig, sstart, send)
        return (contig_data, previous_readname, previous_information)


    with open(mappings) as f:
        previous_readname = set()
        previous_information = ()
        for line in f:
            # Read name, Contig name, percent identity, alignment length, mismatches, 
            # gap openings, query start, query end, subject start, subject end, 
            # e-value, bit score
            # Positions in pblat output are indexed from start (1-indexed)
            # to end (inclusive) so a 75bp read with complete matching
            # could possible have a starting position of 1 and end at 75.
            try:
                (read, contig, identity, length, mismatches, gaps,            #pylint: disable=W0612
                 qstart, qend, sstart, send, evalue, bitscore) = line.split('\t') #pylint: disable=W0612
            except ValueError, e:
                logger.error("Unable to parse results file %s\n%s", mappings, e)
                logger.error("The line that couldn't be parsed was this:\n%s", line)
                raise ParseError("Cannot parse line\n{}\n in file {}".format(line, mappings))
            
            identity = float(identity)
            qend = int(qend)
            qstart = int(qstart)
            aligned_length = abs(qend-qstart)
            sstart = int(sstart)
            send = int(send)

            # Some mappers output reverse coordinates if mapped in the other direction,
            # Reverse them so we do not get negative counts in the coverage      
            if sstart > send:
                sstart, send = (send, sstart)

            logger.debug("Read: {}".format(read))
            read = read.split()[0]
            logger.debug("Formatted to: {}".format(read))

            if options.coverageAllAlignments:
                contig_data, previous_readname, previous_information = check_new_read(contig_data, read, identity, aligned_length, contig, sstart, send, previous_readname, previous_information)
            else:
                contig_data = update_contig_data(contig_data, contig, sstart-1, send, options, logger)


        # Add the last read to contig_data
        check_new_read(contig_data, read, identity, aligned_length, contig, sstart, send, previous_readname, previous_information)

    return contig_data



###############################################
#    Exceptions
###############################################

class Error(Exception):
    """ Base class for exceptions in this module.

    Attributes: 
        msg     error message
    """

    def __init__(self, msg):
        self.msg = msg

class ParseError(Error):
    """ Raised for parsing errors. """

class FileFormatError(Error):
    """ Raised when file is not in expected format. """

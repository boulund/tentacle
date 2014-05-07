"""Tentacle parsers

author:: Fredrik Boulund
date:: 2014-04-30
"""

import numpy as np
from ..coverage import update_contig_data

def parse_razers3(mappings, contig_data, options, logger):
    """ Parses razers3 output.  """
    with open(mappings) as f:
        for line in f:
            # Read name, Read start, Read end, Direction, Contig name, 
            # Contig start, Contig end, percent Identity.
            # Positions in RazerS3 output are indexed from start (0-indexed)
            # to end (non-inclusive) so a 75bp read with complete matching
            # could possible have a starting position of 0 and end at 75.
            try:
                read, rstart, rend, direction, contig, cstart, cend, identity = line.split() #pylint: disable=W0612
            except ValueError, e:
                logger.error("Unable to parse results file %s\n%s", mappings, e)
                logger.error("The line that couldn't be parsed was this:\n%s", line)
                raise ParseError("Cannot parse line\n{}\n in file {}".format(line, mappings))
            cstart = int(cstart)
            cend = int(cend) # End coordinate is non-inclusive

            contig_data = update_contig_data(contig_data, contig, cstart, cend, options, logger)

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

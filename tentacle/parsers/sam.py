"""Tentacle parsers

author:: Fredrik Boulund
date:: 2014-04-30
"""

import numpy as np
from ..coverage import update_contig_data

def parse_sam(mappings, contig_data, options, logger):
    """
    Parses standard SAM alignments.
    Useful for bowtie2 and other aligners that output SAM format
    """
    
    def find_end_pos_from_cigar(cigar):
        """
        Parses a CIGAR string and returns the sum of all entities
        to find the end position of the aligned read in the reference.
        """
        import re
        regex = r'([0-9]+[MIDNSHPX=])'
        allowed_operators = set(['M', 'D', '=', 'X'])
        return sum([int(operator[:-1]) for operator in re.findall(regex, cigar) if operator[-1] in allowed_operators])

    def parse_sam_line(line, contig_data):
        """
        Takes a line, extracts the required information from it
        and updates contig_data accordingly.
        """
        # rname is reference/contig name, pos is starting position of aligned read,
        # end position is extracted from cigar.
        qname, flag, rname, pos, mapq, cigar, rest = line.split(None, 6)
        if rname == '*':
            return contig_data
        else:
            start = int(pos)
            end = start + find_end_pos_from_cigar(cigar) - 1

            contig_data = update_contig_data(contig_data, rname, start-1, end, options, logger)
            return contig_data
                
    with open(mappings) as f:
        line = f.readline()
        if not line.startswith("@HD"):
            logger.error("Unable to parse results file %s\n%s", mappings, e)
            logger.error("Could not find @HD header tag on first line of file:\n%s", line)
            raise ParseError("Mapping results file {} does not start with @HD".format(mappings))
        for line in f:
            if not line.startswith("@"):
                contig_data = parse_sam_line(line, contig_data)
                break # We're in alignment territory and no longer need the check!
        for line in f:
            contig_data = parse_sam_line(line, contig_data)

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

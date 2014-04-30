"""Tentacle parsers

author:: Fredrik Boulund
date:: 2014-04-30
"""

import numpy as np

def parse_gem(mappings, contigCoverage, logger):
    """
    Parses GEM alignment format.
    """

    def find_end_pos_from_gigar(gigar, plus_strand):
        """
        Steps through a GIGAR string and returns the sum of the entities
        that refer to advancements in the reference sequence.
        """
        import re
        regex = r'\d+|\w|>\d+[\+\-\*/\?]|\(\d+\)'

        nucleotides = set(["A", "T", "C", "G"])
        endpos = 0
        entities = re.findall(regex, gigar)
        for entity in entities:
            try:
                endpos += int(entity)
            except ValueError:
                if entity in nucleotides:
                    endpos += 1
                elif entity.startswith(">"):
                    h = re.search(r'\d+', entity)
                    if h is not None:
                        if entity.endswith("+"):
                            if plus_strand:
                                endpos += int(h.group(0))
                            else:
                                endpos -= int(h.group(0))
                        elif entity.endswith("-"):
                            endpos -= int(h.group(0))
                        else:
                            endpos += int(h.group(0))
                    else:
                        logger.error("Cannot parse GIGAR string: {}".format(gigar))
                        raise ParseError("Cannot parse GIGAR string: {}".format(gigar))
                elif entity.startswith("("):
                    pass
        return endpos

    def update_contig_coverage(line, contigCoverage):
        """
        Takes a line, extracts the required information from it
        and updates contigCoverage accordingly.
        """
        # reference contig, start, and end position are extracted from gigar string.
        readname, readseq, readqual, matchsummary, alignments = line.split("\t", 4) 
        if alignments.startswith("-"):
            return contigCoverage
        else:
            # We only use the first alignment if there are several
            alignments = alignments.split(",")[0] 
            try:
                contigname, strand, startpos, gigar = alignments.split(":")
                if strand == "+": 
                    plus_strand = True
                else:
                    plus_strand = False
            except ValueError:
                logger.error("Cannot split alignment information: '{}'".format(alignments))
                raise ParseError("Cannot split alignment information: {}".format(alignments))
            startpos = int(startpos)
            end = startpos + find_end_pos_from_gigar(gigar, plus_strand) - 1

            contigCoverage[contigname][0][startpos-1] += 1
            contigCoverage[contigname][0][end] += -1
            contigCoverage[contigname][1] += 1 # Number of mapped reads
            return contigCoverage

    with open(mappings) as f:
        for line in f:
            contigCoverage = update_contig_coverage(line, contigCoverage)
    return contigCoverage


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

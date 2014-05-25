# coding: utf-8
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
"""Tentacle parsers

author:: Fredrik Boulund
date:: 2014-04-30
"""

import numpy as np
from ..coverage import update_contig_data

def parse_gem(mappings, contig_data, options, logger):
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

    def parse_gem_line(line, contig_data):
        """
        Takes a line, extracts the required information from it
        and updates contig_data accordingly.
        """
        # reference contig, start, and end position are extracted from gigar string.
        readname, readseq, readqual, matchsummary, alignments = line.split("\t", 4) 
        if alignments.startswith("-"):
            return contig_data
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
            endpos = startpos + find_end_pos_from_gigar(gigar, plus_strand) - 1

            return (contigname, startpos, endpos)

    with open(mappings) as f:
        for line in f:
            contigname, startpos, endpos = parse_gem_line(line, contig_data)
            contig_data = update_contig_data(contig_data, contigname, startpos-1, endpos, options, logger)
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

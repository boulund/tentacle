"""Tentacle coverage module.

.. moduleauthor:: Fredrik Boulund <fredrik.boulund@chalmers.se>

date: 2014-04-30

"""
import numpy as np

def update_contig_data(contig_data, contig, rstart, rend, options, logger):
    """ Updates mapping data for contig.
    
    Use 0-based starting positions and non-inclusive end positions (like Python)."""

    if options.discardSequencesShorterThan:
        aligned_length = rend - rstart
        if aligned_length < int(options.discardSequencesShorterThan):
            logger.debug("Removed read with length {}".format(aligned_length))
            return contig_data

    if not options.noCoverage:
        # Add 1 at the starting position of the mapped read and 
        # subtract 1 at the end so that we later can compute the 
        # cumulative sum from left to right across the entire contig.
        contig_data[contig]["__coverage__"][rstart] += 1
        contig_data[contig]["__coverage__"][rend] += -1

    if not options.noCounts:
        annotations_matched = determine_if_read_is_inside_region(contig_data, contig, rstart, rend, options, logger)
        for annotation in annotations_matched:
            contig_data[contig][annotation][0] += 1 # Number of mapped reads

    return contig_data

def determine_if_read_is_inside_region(contig_data, contig, rstart, rend, options, logger):
    """ Determines if a read lies within an annotated region of a contig. """

    rstart = rstart+1 # Annotations have 1-based numbers
    annotations_matched = []

    for annotation in contig_data[contig].keys():
        if rend - rstart + 1 >= options.coverageReadOverlap:
            a_start = contig_data[contig][annotation][1] + options.coverageReadOverlap
            a_end = contig_data[contig][annotation][2] - options.coverageReadOverlap
            
            if rend >= a_start and rend <= a_end:
                annotations_matched.append(annotation)
            elif rstart >= a_start and rstart <= a_end:
                annotations_matched.append(annotation)

    return annotations_matched


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

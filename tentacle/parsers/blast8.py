"""Tentacle parsers blast tabular output

author:: Fredrik Boulund
date:: 2014-04-30
"""

import numpy as np

def parse_blast8(mappings, contigCoverage, options, logger):
    """
    Parses mapped data in blast8 format (used for blast and pblat) and fills the
    contigCoverage dictionary
    """
    #DEBUG
    #np.set_printoptions(threshold='nan') 

    def update_contigCoverage(contig, sstart, send):
        """ Updates contigCoverage. """
        # Add 1 at the starting position of the mapped read and 
        # subtract 1 at the end so that we later can compute the 
        # cumulative sum from left to right across the entire contig.
        contigCoverage[contig][0][sstart-1] += 1
        contigCoverage[contig][0][send] += -1
        contigCoverage[contig][1] += 1 # Number of mapped reads


    def check_new_read(read, identity, aligned_length, contig, sstart, send, previous_read, previous_information):
        """ Determines if the most recently parsed read has been seen before """
        # We cannot assume the output is ordered so 
        # check if readname has already been seen and 
        # determine if the new hit is better before 
        # committing to contigCoverage.
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
                logger.debug("Read {} with stats {}, {}, {}, {}, {}, was best hit, committing to contigCoverage".format(
                                previous_readname, previous_information[0], previous_information[1], previous_information[2], previous_information[3], previous_information[4]))
                _, _, contig, sstart, send = previous_information
                update_contigCoverage(contig, sstart, send)
            previous_readname.clear()
            previous_readname.add(read)
            previous_information = (identity, aligned_length, contig, sstart, send)
        return (previous_readname, previous_information)


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

            if options.mapperName == "usearch":
                if options.usearchFilterSequencesShorterThan:
                    if aligned_length < int(options.usearchFilterSequencesShorterThan):
                        logger.debug("Removed read '{}' with length {}".format(read, aligned_length))
                        continue
            
            logger.debug("Read: {}".format(read))
            read = read.split()[0]
            logger.debug("Formatted to: {}".format(read))

            if options.coverageAllAlignments:
                previous_readname, previous_information = check_new_read(read, identity, aligned_length, contig, sstart, send, previous_readname, previous_information)
            else:
                update_contigCoverage(contig, sstart, send)

            # DEBUG
            #if np.min(np.cumsum(contigCoverage[contig])) < 0:
            #    print read, contig, qstart, qend, sstart, send
            #    print contigCoverage[contig]
            #    exit(1)
        
        # Add the last read to contigCoverage
        try:
            check_new_read(read, identity, aligned_length, contig, sstart, send, previous_readname, previous_information)
        except UnboundLocalError:
            logger.info("Mappings file {} appears to be empty".format(mappings))

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

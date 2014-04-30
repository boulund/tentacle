"""Tentacle coverage module.

.. moduleauthor:: Fredrik Boulund <fredrik.boulund@chalmers.se>
.. date:: 2014-04-30

"""
import numpy as np
from ..parsers import blast8, razers3, sam, gem 
from statistics import compute_coverage_statistics

def sumMapCounts(mappings, contigCoverage, options, logger):
    """
    Adds the number of mapped reads to the correct positions in 
    a contigCoverage dictionary.

    Uses NumPy.

    Input:
        mappings    mapper output file.
        contigCoverage  the contigCoverage dictionary
        options     all options
        logger      a logger object
    Output:
        contigCoverage 
    """
    if options.mapperName in ("pblat", "blast", "usearch"):
        contigCoverage = blast8.parse_blast8(mappings, contigCoverage, options, logger)
    elif options.mapperName == "razers3":
        contigCoverage = razers3.parse_razers3(mappings, contigCoverage, logger)
    elif options.mapperName == "bowtie2":
        contigCoverage = sam.parse_sam(mappings, contigCoverage, logger)
    elif options.mapperName == "gem":
        contigCoverage = gem.parse_gem(mappings, contigCoverage, logger)
    else:
        logger.error("Couldn't figure out what mapper was used! This should never happen?!")
        exit(1)

    for contig in contigCoverage.keys():
        np.cumsum(contigCoverage[contig][0], dtype=np.int32, out=contigCoverage[contig][0])
    return contigCoverage


def computeAnnotationCounts(annotationFilename, contigCoverage, outFilename, logger):
    """
    Produces counts for each annotated region. Writes results to file.

    Input:
        annotationFilename  filename of annotation file
        contigCoverage      the contigCoverage dictionary
        outFilename         output filename
        logger              a logger object object
    Output:
        None                Writes directly to file
    Raises:
        ParseError          On parsing errors
    """
    
    with open(annotationFilename) as annotationFile:
        logger.debug("Parsing {}".format(annotationFilename))
        with open(outFilename, "w") as outFile:
            # Initialize dictionary for storage of annotation counts
            annotationCounts = {}
            for line in annotationFile:
                try:
                    contig, start, end, strand, annotation = line.split()
                except ValueError, e:
                    logger.error("Could not parse annotation line\n{}\nfrom file {}".format(line, annotationFilename))
                    raise ParseError("Could not parse line {} in file {}".format(line, annotationFilename))
                    
                start = int(start)-1
                end = int(end)

                try:
                    stats = compute_coverage_statistics(contigCoverage[contig][0][start:end])
                    outFile.write(contig+"_"+annotation+":"+str(start)+":"+str(end)+":"+strand+"\t"+
                                  str(contigCoverage[contig][1])+"\t"+
                                  str(stats[0])+"\t"+
                                  str(stats[1])+"\t"+
                                  str(stats[2])+"\n")
                except KeyError, contigHeader:
                    logger.error("Could not find match for contig header {0} in annotation file {1}.".format(contigHeader, annotationFilename))
                    raise ParseError("Header {} not found in annotation file {}".format(contigHeader, annotationFilename))


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

###############################################
#    DEBUG
###############################################
def _printAnnotationCounts(annotationCounts, outputFile=""):
    """
    Debug function that prints annotationCounts to stdout or file.
    WARNING EXTREMELY SLOW
    """
    if outputFile:
        with open(outputFile, "w") as file:
            for annotation in annotationCounts.keys():

                info = [annotation, 
                        annotationCounts[annotation][0],
                        annotationCounts[annotation][1],
                        annotationCounts[annotation][2]]
                info = [str(text) for text in info]
                file.write('\t'.join(info))
                file.write('\n')
    else:
        print "\n\nAnnotation\tMedian\tMean\tStdev"
        for annotation in annotationCounts.keys():
            info = [annotation, 
                    annotationCounts[annotation][0],
                    annotationCounts[annotation][1],
                    annotationCounts[annotation][2]]
            info = [str(text) for text in info]
            print '\t'.join(info)

"""Tentacle coverage module.

.. moduleauthor:: Fredrik Boulund <fredrik.boulund@chalmers.se>
.. date:: 2014-04-30

"""
import numpy as np
from statistics import compute_region_statistics


def update_contig_data(contig_data, contig, rstart, rend, options, logger):
    """ Updates mapping data for contig.
    
    Use 0-based starting positions and non-inclusive end positions (like Python)."""
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
        a_start = contig_data[contig][annotation][1]
        a_end = contig_data[contig][annotation][2]
        # TODO: Extend using options to determine overlap requirements
        if rend >= a_start and rend <= a_end:
            annotations_matched.append(annotation)
        elif rstart >= a_start and rstart <= a_end:
            annotations_matched.append(annotation)
    return annotations_matched


def compute_and_write_coverage_statistics(annotationFilename, contig_data, outFilename, options, logger):
    """ Computes coverage for each annotated region. Writes results to file.

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

    outFile = open(outFilename, "w")
    logger.debug("Writing to {}.".format(outFilename))
    for contig in contig_data.keys():
        for annotation in contig_data[contig].keys():
            if "__coverage__" in annotation:
                pass
            else:
                count, start, end, strand = contig_data[contig][annotation]
                if options.noCoverage:
                    stats = ["N", "N", "N"]
                else: 
                    stats = compute_region_statistics(contig_data[contig]["__coverage__"][start:end])

                if options.noCounts:
                    annotation_count = "N"
                else:
                    annotation_count = contig_data[contig][annotation][0]

                try:
                    outFile.write("{}_{}:{}:{}:{}\t{}\t{}\t{}\t{}\n".format(contig,
                            annotation,
                            str(start),
                            str(end),
                            strand,
                            str(annotation_count),
                            str(stats[0]),
                            str(stats[1]),
                            str(stats[2]))
                            )
                except KeyError, contigHeader:
                    logger.error("Could not find match for contig header {} in annotation file {}.".format(contigHeader, annotationFilename))
                    raise ParseError("Header {} not found in annotation file {}".format(contigHeader, annotationFilename))




def debug_output_coverage(logger, output_filename, contig_coverage):
    """Debug function to write out the numpy arrays for manual inspection. WARNING: SLOOOW!"""
    if options.outputCoverage:
        np.set_printoptions(threshold='nan', linewidth='inf')
        logger.debug("Writing complete coverage maps to {} (this is sloooow!)".format(output_filename))
        with open(output_filename, "w") as coverageFile:
            for contig in contig_coverage.keys():
                coverageFile.write('\t'.join([contig, str(contig_coverage[contig])+"\n"]))
        logger.debug("Coverage maps written to {}.".format(output_filename))

def debug_print_single_coverage(contig_coverage, contig, annotation=False):
    """ Debug function to print a single contigs numpy array and additional annotation information."""
    np.set_printoptions(threshold='nan', linewidth='inf')
    if annotation: 
        print contig_coverage[contig][annotation]
    print contig_coverage[contig]["__coverage__"]

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

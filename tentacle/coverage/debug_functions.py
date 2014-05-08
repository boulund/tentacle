
"""Tentacle coverage module: debug functions.

.. moduleauthor:: Fredrik Boulund <fredrik.boulund@chalmers.se>
.. date:: 2014-04-30

"""
import numpy as np

def debug_output_coverage(logger, output_filename, contig_coverage):
    """Debug function to write out the numpy arrays for manual inspection. WARNING: SLOOOW!"""
    if options.outputCoverage:
        np.set_printoptions(threshold='nan', linewidth='inf')
        logger.debug("Writing complete coverage maps to {} (this is sloooow!)".format(output_filename))
        with open(output_filename, "w") as coverageFile:
            for contig in contig_coverage.keys():
                coverageFile.write('\t'.join([contig, str(contig_coverage[contig])+"\n"]))
        logger.debug("Coverage maps written to {}.".format(output_filename))

def debug_print_single_coverage(contig_data, contig):
    """ Debug function to print a single contigs numpy array and additional annotation information."""
    np.set_printoptions(threshold='nan', linewidth='inf')
    print "Annotations and coverage for sequence '{}'".format(contig)
    for annotation in contig_data[contig].keys():
        print annotation, contig_data[contig][annotation]

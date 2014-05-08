"""Tentacle coverage module: compute coverage statistics

.. moduleauthor:: Fredrik Boulund <fredrik.boulund@chalmers.se>
.. date:: 2014-04-30
.. purpose:: Writes results to file, and computes coverage statistics 

"""
from statistics import compute_region_statistics

def compute_and_write_coverage_statistics(annotationFilename, contig_data, outFilename, options, logger):
    """ Computes coverage for each annotated region. Writes results to file.

    Input:
        annotationFilename  filename of annotation file
        contig_data         the contig_data dictionary
        outFilename         output filename
        options             options namespace
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

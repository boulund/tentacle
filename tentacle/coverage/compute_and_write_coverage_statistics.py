"""Tentacle coverage module: compute coverage statistics

author: Fredrik Boulund <fredrik.boulund@chalmers.se>
date: 2014-04-30
purpose: Writes results to file, and computes coverage statistics 

"""
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

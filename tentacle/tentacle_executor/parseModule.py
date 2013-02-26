#!/usr/bin/env python
# Fredrik Boulund 2012

from sys import argv, exit
import numpy as np
import logging

# Define a logger 
#logger = logging.getLogger("Tentacle.parseModule")


def indexContigs(contigsFile, logger):
    """
    Creates a dictionary indexed by first-space separated header string
    in both single and multiline FASTA files.

    Uses NumPy to store the arrays with coverage information.
    Each position in the dictionary, indexed by header string, contains
    a single list of length equal to contig length+1 for use in coverage
    computations.
    """

    contigCoverage = {} 
    # Parse contigsFile to fill out data structure
    with open(contigsFile) as file:
        line = file.readline().strip()
        # Check that contigsFile seems to be in FASTA format
        if not line.startswith(">"):
            logger.error("CONTIGS file %s not in FASTA format?", contigsFile)
            exit(1)
        while line != "":
            if line.startswith(">"):
                header = line.split()[0][1:]

                # Read the next line to start counting sequence length
                seqlength = 0

                # Start reading contig length
                line = file.readline().strip()
                while True:
                    if line.startswith(">"):
                        # Create a list of zeros for current contig ("header")
                        # It is one element longer than the number of bases 
                        # in the contig.
                        contigCoverage[header] = np.zeros(seqlength+1)
                        break
                    else:
                        # Prepared for contig sequences in multi-line FASTA.
                        # This will sum the number of
                        # bases (characters) for each line together
                        seqlength = seqlength + len(line)
                        line = file.readline().strip()
                        if line == "":
                            # Finish the last contig
                            contigCoverage[header] = np.zeros(seqlength+1)
                            break

    return contigCoverage


def parse_razers3(mappings, contigCoverage, logger):
    """
    Parses razers3 output and fills the
    contigCoverage dictionary
    """
    with open(mappings) as file:
        for line in file:
            # Read name, Read start, Read end, Direction, Contig name, 
            # Contig start, Contig end, percent Identity.
            # Positions in RazerS3 output are indexed from start (0-indexed)
            # to end (non-inclusive) so a 75bp read with complete matching
            # could possible have a starting position of 0 and end at 75.
            try:
                read, rstart, rend, direction, contig, cstart, cend, identity = line.split()
            except ValueError, e:
                logger.error("Unable to parse results file %s\n%s", mappings, e)
                exit(1)
            cstart = int(cstart)
            cend = int(cend) # End coordinate is non-inclusive

            # Add 1 at the starting position of the mapped read and subtract
            # 1 at the end so that we later can compute the cumulative sum
            # from left to right across the entire contig. Note that the end
            # position is non-inclusive and thus already +1:ed.
            contigCoverage[contig][cstart] = contigCoverage[contig][cstart]+1
            contigCoverage[contig][cend] = contigCoverage[contig][cend]-1

    for contig in contigCoverage.keys():
        contigCoverage[contig] = np.cumsum(contigCoverage[contig])

    return contigCoverage


def parse_pblat_blast8(mappings, contigCoverage, logger):
    """
    Parses pblat output (blast8 format) and fills the
    contigCoverage dictionary
    """

    with open(mappings) as file:
        for line in file:
            # Read name, Contig name, percent identity, alignment length, mismatches, 
            # gap openings, query start, query end, subject start, subject end, 
            # e-value, bit score
            # Positions in pblat output are indexed from start (1-indexed)
            # to end (inclusive) so a 75bp read with complete matching
            # could possible have a starting position of 1 and end at 75.
            try:
                read, contig, identity, length, mismatches, gaps, \
                    qstart, qend, sstart, send, evalue, bitscore= line.split()
            except ValueError, e:
                logger.error("Unable to parse results file %s\n%s", mappings, e)
                exit(1)
            sstart = int(sstart)
            send = int(send)

            # Add 1 at the starting position of the mapped read and subtract
            # 1 at the end so that we later can compute the cumulative sum
            # from left to right across the entire contig.
            contigCoverage[contig][sstart] = contigCoverage[contig][sstart-1]+1
            contigCoverage[contig][send] = contigCoverage[contig][send]-1

    for contig in contigCoverage.keys():
        contigCoverage[contig] = np.cumsum(contigCoverage[contig])

    return contigCoverage

def sumMapCounts(mappings, contigCoverage, pblat, logger):
    """
    Adds the number of mapped reads to the correct positions in 
    a contigCoverage dictionary.
    Uses NumPy.
    """
    if pblat:
        contigCoverage = parse_pblat_blast8(mappings, contigCoverage, logger)
    else:
        contigCoverage = parse_razers3(mappings, contigCoverage, logger)
    return contigCoverage



def computeAnnotationCounts(annotationFilename, contigCoverage, outFilename, logger):
    """
    Produces counts for each annotated region.
    (Does not yet) Writes results to file.
    """
    
    with open(annotationFilename) as annotationFile:
        with open(outFilename, "w") as outFile:
            # Initialize dictionary for storage of annotation counts
            annotationCounts = {}
            for line in annotationFile:
                contig, start, end, strand, annotation = line.split()
                start = int(start)
                end = int(end)

                ## DEBUG: Print all annotations that are nonzero
                ## WARNING, prints A LOT!
                #if computeStatistics(contigCoverage[contig][start:end])[1] != 0:
                #    print contig
                #    print contigCoverage[contig][start:end]
                #    print computeStatistics(contigCoverage[contig][start:end])

                try:
                    stats = computeStatistics(contigCoverage[contig][start:end])
                except KeyError, message:
                    logger.error("Could not find contig header in annotation file.\n%s", message)
                    logger.error("Maybe the contig headers do not match the annotation file?")
                    exit(1)
                outFile.write(contig+"_"+annotation+":"+str(start)+":"+str(end)+":"+strand+"\t"+
                              str(stats[0])+"\t"+
                              str(stats[1])+"\t"+
                              str(stats[2])+"\n")

    # No need to return anything when writing to file directly
    #return annotationCounts



def computeStatistics(region):
    """
    Compute general statistics of reads mapped to a region of a contig.

    Input:
        region  a NumPy array of ints with the number of reads mapped
                to the region.
    Output:
        median  (float) the median number of reads mapped to the region.
        mean    (float) the mean numbr of reads mapped to the region.
        stdev   (float) the standard deviation of number of reads
                mapped to the region.
    """
    return (np.median(region), np.mean(region), np.std(region))



def printAnnotationCounts(annotationCounts, outputFile=""):
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
                            
                            

if __name__ == "__main__":
    if len(argv)<2:
        print "Usage:", argv[0], "CONTIGS MAPPINGRESULTS ANNOTATION"
        print "Running this file stand-alone is deprecated and will probably not work!"

    contigCoverage = indexContigs(argv[1])

    contigCoverage = sumMapCounts(argv[2], contigCoverage)

    #set_printoptions(threshold='nan')
    #print contigCoverage["scaffold1309_7_MH0014"]

    annotationCounts = computeAnnotationCounts(argv[3], contigCoverage)


# Fredrik Boulund 2012

import numpy as np

def indexContigs(contigsFile, logger):
    """
    Creates a dictionary indexed by first-space separated header string
    in both single and multiline FASTA files.

    Uses NumPy to store the arrays with coverage information.
    Each position in the dictionary, indexed by header string, contains
    a single list of length equal to contig length+1 for use in coverage
    computations.
    """

    array_size = 0
    contigCoverage = {} 
    # Parse contigsFile to fill out data structure
    with open(contigsFile) as f:
        line = f.readline().strip()
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
                line = f.readline().strip()
                while True:
                    if line.startswith(">"):
                        # Create a list of zeros for current contig ("header")
                        # It is one element longer than the number of bases 
                        # in the contig.
                        contigCoverage[header] = np.zeros(seqlength+1, dtype=np.uint16)
                        array_size += contigCoverage[header].nbytes
                        break
                    else:
                        # Prepared for contig sequences in multi-line FASTA.
                        # This will sum the number of bases (characters) 
                        # for each line 
                        seqlength = seqlength + len(line)
                        line = f.readline().strip()
                        if line == "":
                            # Finish the last contig
                            contigCoverage[header] = np.zeros(seqlength+1, dtype=np.uint16)
                            array_size += contigCoverage[header].nbytes
                            break

    logger.debug("Sum of all numpy array sizes: {}".format(array_size))
    return contigCoverage


def parse_sam(mappings, contigCoverage, logger):
    """
    Parses standard SAM alignments.
    Useful for bowtie2 and other aligners that output SAM format
    """
    
    def find_end_pos_from_cigar(cigar):
        """
        Parses a CIGAR string and returns the sum of all entities
        to find the end position of the aligned read in the reference.
        """
        import re
        regex = r'([0-9]+[MIDNSHPX=])'
        allowed_operators = set(['M', 'D', '=', 'X'])
        return sum([int(operator[:-1]) for operator in re.findall(regex, cigar) if operator[-1] in allowed_operators])

    def update_contig_coverage(line, contigCoverage):
        """
        Takes a line, extracts the required information from it
        and updates contigCoverage accordingly.
        """
        # rname is reference/contig name, pos is starting position of aligned read,
        # end position is extracted from cigar.
        qname, flag, rname, pos, mapq, cigar, rest = line.split(None, 6)
        if rname == '*':
            return contigCoverage
        else:
            start = int(pos)
            end = start + find_end_pos_from_cigar(cigar) - 1
            contigCoverage[rname][start-1] += 1
            contigCoverage[rname][end] += -1
            return contigCoverage
                
    with open(mappings) as f:
        line = f.readline()
        if not line.startswith("@HD"):
            logger.error("Unable to parse results file %s\n%s", mappings, e)
            logger.error("Could not find @HD header tag on first line of file")
            exit(1)
        for line in f:
            if not line.startswith("@"):
                contigCoverage = update_contig_coverage(line, contigCoverage)
                break # We're in alignment territory and no longer need the check!
        for line in f:
            contigCoverage = update_contig_coverage(line, contigCoverage)

    return contigCoverage


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
                        exit(1)
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
                logger.error("Unable to split alignment information: '{}'".format(alignments))
                exit(1)
            startpos = int(startpos)
            end = startpos + find_end_pos_from_gigar(gigar, plus_strand) - 1

            contigCoverage[contigname][startpos-1] += 1
            contigCoverage[contigname][end] += -1
            return contigCoverage

    with open(mappings) as f:
        for line in f:
            contigCoverage = update_contig_coverage(line, contigCoverage)
    return contigCoverage


def parse_razers3(mappings, contigCoverage, logger):
    """
    Parses razers3 output and fills the
    contigCoverage dictionary
    """
    with open(mappings) as f:
        for line in f:
            # Read name, Read start, Read end, Direction, Contig name, 
            # Contig start, Contig end, percent Identity.
            # Positions in RazerS3 output are indexed from start (0-indexed)
            # to end (non-inclusive) so a 75bp read with complete matching
            # could possible have a starting position of 0 and end at 75.
            try:
                read, rstart, rend, direction, contig, cstart, cend, identity = line.split() #pylint: disable=W0612
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

    return contigCoverage


def parse_blast8(mappings, contigCoverage, logger):
    """
    Parses mapped data in blast8 format (used for blast and pblat) and fills the
    contigCoverage dictionary
    """
    #np.set_printoptions(threshold='nan') #DEBUG

    with open(mappings) as f:
        previous_readname = set()
        for line in f:
            # Read name, Contig name, percent identity, alignment length, mismatches, 
            # gap openings, query start, query end, subject start, subject end, 
            # e-value, bit score
            # Positions in pblat output are indexed from start (1-indexed)
            # to end (inclusive) so a 75bp read with complete matching
            # could possible have a starting position of 1 and end at 75.
            try:
                (read, contig, identity, length, mismatches, gaps,            #pylint: disable=W0612
                 qstart, qend, sstart, send, evalue, bitscore) = line.split() #pylint: disable=W0612
            except ValueError, e:
                logger.error("Unable to parse results file %s\n%s", mappings, e)
                exit(1)

            # Reads are ordered in the pblat output so we can safely assume no read will
            # occur twice in the file if it has been previously seen. We can thus conserve 
            # memory by removing previous reads from the set.
            if read not in previous_readname:
                previous_readname.clear() 
                previous_readname.add(read) 

                # pblat outputs reverse coordinates if mapped in the other direction,
                # The are reversed so we do not get negative counts
                sstart = int(sstart)
                send = int(send)
                if sstart > send:
                    sstart, send = (send, sstart)

                # Add 1 at the starting position of the mapped read and subtract
                # 1 at the end so that we later can compute the cumulative sum
                # from left to right across the entire contig.
                contigCoverage[contig][sstart-1] = contigCoverage[contig][sstart-1]+1
                contigCoverage[contig][send] = contigCoverage[contig][send]-1
                
                # DEBUG
                #if np.min(np.cumsum(contigCoverage[contig])) < 0:
                #    print read, contig, qstart, qend, sstart, send
                #    print contigCoverage[contig]
                #    exit(1)

    return contigCoverage


def sumMapCounts(mappings, contigCoverage, options, logger):
    """
    Adds the number of mapped reads to the correct positions in 
    a contigCoverage dictionary.
    Uses NumPy.
    """
    if options.pblat:
        contigCoverage = parse_blast8(mappings, contigCoverage, logger)
    elif options.blast:
        contigCoverage = parse_blast8(mappings, contigCoverage, logger)
    elif options.razers3:
        contigCoverage = parse_razers3(mappings, contigCoverage, logger)
    elif options.bowtie2:
        contigCoverage = parse_sam(mappings, contigCoverage, logger)
    elif options.gem:
        contigCoverage = parse_gem(mappings, contigCoverage, logger)
    else:
        logger.error("No mapper selected! This should never happen?!")
        exit(1)

    for contig in contigCoverage.keys():
        np.cumsum(contigCoverage[contig], dtype=np.uint16, out=contigCoverage[contig])
    return contigCoverage



def computeAnnotationCounts(annotationFilename, contigCoverage, outFilename, logger):
    """
    Produces counts for each annotated region.
    Writes results to file.
    """
    
    with open(annotationFilename) as annotationFile:
        with open(outFilename, "w") as outFile:
            # Initialize dictionary for storage of annotation counts
            annotationCounts = {}
            for line in annotationFile:
                contig, start, end, strand, annotation = line.split()
                start = int(start)-1
                end = int(end)

                ## DEBUG: Print all annotations that are nonzero
                ## WARNING, prints A LOT!
                #if computeStatistics(contigCoverage[contig][start:end])[1] != 0:
                #    print contig
                #    print start, end
                #    print contigCoverage[contig][start:end]
                #    print computeStatistics(contigCoverage[contig][start:end])

                try:
                    stats = computeStatistics(contigCoverage[contig][start:end])
                except KeyError, contigHeader:
                    logger.error("Could not find match for contig header '{0}' in annotation file {1}".format(contigHeader, annotationFilename))
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

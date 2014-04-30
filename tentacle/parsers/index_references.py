"""Tentacle indexContigs

author:: Fredrik Boulund
date:: 2014-04-30
purpose:: Indexes contigsFiles to produce the data structure that holds contigCoverage
          
"""
import numpy as np

def create_contigCoverage(contigsFile, logger):
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
        # Check that contigsFile seems to be in FASTA format
        line = f.readline().strip()
        if not line.startswith(">"):
            logger.error("CONTIGS file %s not in FASTA format?", contigsFile)
            logger.error("First line is this:\n%s", line)
            raise FileFormatError("{} not in FASTA format?".format(contigsFile))

        header = line.split()[0][1:]

        # Start reading contig length
        seqlength = 0
        line = f.readline().strip()
        while True:
            if line.startswith(">"):
                # Create a list of zeros for current contig ("header")
                # It is one element longer than the number of bases 
                # in the contig.
                contigCoverage[header] = [np.zeros(seqlength+1, dtype=np.int32), 0]
                array_size += contigCoverage[header][0].nbytes

                # Reinit for next sequence
                seqlength = 0
                header = line.split()[0][1:]
                line = f.readline()
            else:
                # Prepared for contig sequences in multi-line FASTA.
                # This will sum the number of bases for each line 
                seqlength = seqlength + len(line.strip())
                line = f.readline()
                if line == "":
                    # Finish the last contig
                    contigCoverage[header] = [np.zeros(seqlength+1, dtype=np.int32), 0]
                    array_size += contigCoverage[header][0].nbytes
                    break

    logger.debug("Sum of all numpy array sizes: {}".format(array_size))
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

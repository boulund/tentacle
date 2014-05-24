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
"""Tentacle initialize contig data structure

author:: Fredrik Boulund
date:: 2014-05-06
purpose:: Creates an empty data structure for contig coverage and annotated region count information.
          
"""
import numpy as np

def initialize_contig_data(files, options, logger):
    """ Reads annotation and reference (FASTA) files to create an empty data structure.

    Data structure is a nested dictionary:
     contig_data                 MAIN DICTIONARY
       ["CONTIG0101"]            CONTIG KEY
         ["TIGRFAM0101"]         ANNOTATION KEY
           [int, int, int, "+"]  LIST WITH: [ANNOTATION COUNT, ANNOTATION START, ANNOTATION STOP, STRAND]
         ["__coverage__"]        COVERAGE SPECIAL KEY (if reference sequence has this name error ensues!)
           np.array              COVERAGE DATA STRUCTURE (NumPy array)
    """
    logger.info("Initializing coverage data structure...")
    contig_data = {}
    contig_data = initialize_contig_keys(contig_data, files.contigs, options, logger)
    contig_data = initialize_annotation_counts(contig_data, files.annotations, options, logger)
    logger.info("Coverage data structure initialized.")
    return contig_data


def initialize_contig_keys(contig_data, contigs_file, options, logger):
    """ Creates the first level of keys in the contig_data dictionary from a FASTA file.

    Keys in the dictionary are based on the first-space separated header
    string in the FASTA headers.

    Each sequence is represented by a continous array of length equal to 
    contig length+1 for later use in coverage computations.
    """

    def initialize_coverage_array(seqlength, datatype):
        """ Initializes a numpy array for use in coverage computations. """
        return np.zeros(seqlength+1, dtype=datatype)

    if not options.noCoverage:
        arrays_size = 0
    # Parse contigs_file to fill out data structure
    with open(contigs_file) as f:
        # Check that contigs_file seems to be in FASTA format
        line = f.readline().strip()
        if not line.startswith(">"):
            logger.error("CONTIGS file %s not in FASTA format?", contigs_file)
            logger.error("First line is this:\n%s", line)
            raise FileFormatError("{} not in FASTA format?".format(contigs_file))

        # Strip everything after the first space
        header = line.split()[0][1:]

        # Start reading sequence data to determine contig length
        seqlength = 0
        line = f.readline().strip()
        while True:
            if line.startswith(">"):
                # Create the first level of keys in the contig_data structure
                contig_data[header] = {}
                if not options.noCoverage:
                    contig_data[header]["__coverage__"] = initialize_coverage_array(seqlength, np.int32)
                    arrays_size += contig_data[header]["__coverage__"].nbytes

                # Reinit for next sequence
                seqlength = 0
                header = line.split()[0][1:]
                line = f.readline()
            else:
                # For reference sequences in multi-line FASTA.
                # This will sum the number of bases for each line 
                seqlength = seqlength + len(line.strip())
                line = f.readline()
                if line == "":
                    # Finish the last contig
                    contig_data[header] = {}
                    if not options.noCoverage:
                        contig_data[header]["__coverage__"] = initialize_coverage_array(seqlength, np.int32)
                        arrays_size += contig_data[header]["__coverage__"].nbytes
                    break

    if not options.noCoverage:
        logger.debug("Sum of all numpy array sizes: {} bytes".format(arrays_size))
    return contig_data


def initialize_annotation_counts(contig_data, annotations_filename, options, logger):
    """ Initializes the second level of keys in the contig_data structure (annotations)."""
    with open(annotations_filename) as annotations_file:
        logger.debug("Parsing {}.".format(annotations_filename))
        for line in annotations_file:
            try:
                contig_header, start, end, strand, annotation = line.split()
            except ValueError, e:
                logger.error("Could not parse annotation line\n{}\nfrom file {}.".format(line, annotations_filename))
                raise ParseError("Could not parse line {} in file {}.".format(line, annotations_filename))

            start = int(start) # Uses 0-based indexing
            end = int(end)
            contig_data[contig_header][annotation] = [0, start, end, strand]

    return contig_data


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

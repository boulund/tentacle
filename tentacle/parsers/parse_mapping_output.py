"""Tentacle parse mapping output and compute coverage/counts.

author:: Fredrik Boulund
date:: 2014-05-07<F5>
purpose:: Parses mapping output in different formats and extracts mapped read information
          used in coverage/counts computations..
          
"""
import numpy as np
import blast8
import razers3
import sam
import gem

def parse_mapping_output(mappings, contig_data, options, logger):
    """
    Adds the number of mapped reads to the correct positions in 
    a contig_data dictionary.

    Uses NumPy.

    Input:
        mappings    mapper output file.
        contig_data  the contig_data dictionary
        options     all options
        logger      a logger object
    Output:
        contig_data 
    """
    if options.mapperName in ("pblat", "blast", "usearch"):
        contig_data = blast8.parse_blast8(mappings, contig_data, options, logger)
    elif options.mapperName == "razers3":
        contig_data = razers3.parse_razers3(mappings, contig_data, options, logger)
    elif options.mapperName == "bowtie2":
        contig_data = sam.parse_sam(mappings, contig_data, options, logger)
    elif options.mapperName == "gem":
        contig_data = gem.parse_gem(mappings, contig_data, options, logger)
    else:
        logger.error("Couldn't figure out what mapper was used! This should never happen?!")
        exit(1)

    for contig in contig_data.keys():
        np.cumsum(contig_data[contig]["__coverage__"], dtype=np.int32, out=contig_data[contig]["__coverage__"])
    return contig_data

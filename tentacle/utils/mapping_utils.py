#!/usr/bin/env python2.7
# Fredrik Boulund 2013
# Anders Sjogren 2013

from sys import exit, stdout
from subprocess import PIPE#, Popen
import os
import shutil

from gevent.subprocess import Popen
#import gevent
#gevent.monkey.patch_subprocess()
import psutil

from .. import utils

def copy_untar_ref_db(source_file, destination, logger):
    """
    Copies and uncompresses gzipped tar file containing reference database to destination.
    """

    workdir = os.path.dirname(destination)
    tar_call = [utils.resolve_executable("tar"), "-xf", source_file]

    if source_file.lower().endswith((".tar.gz", ".tar", ".tgz")):
        logger.info("It appears reference DB '%s' is in tar/gz format", source_file)
        logger.info("Extracting (and if necessary gunzipping) database...")
        shutil.copy(source_file, destination)
        tar = Popen(tar_call, stdout=PIPE, stderr=PIPE, cwd=workdir)
        logger.debug("tar call:{}".format(tar_call))
        tar_stream_data = tar.communicate()
        if tar.returncode is not 0:
            logger.error("{}".format(tar_stream_data))
            logger.error("tar returncode {}".format(tar.returncode))
            logger.error("tar stdout: {}\nstderr: {}".format(tar_stream_data))
            exit(1)
        else:
            logger.info("Untar of reference DB successful.")
    elif source_file.lower().endswith((".gz")):
        logger.info("It appears reference DB '%s' is in gz format", source_file)
        logger.info("Gunzipping databsae...")
        shutil.copy(source_file, destination)
        gunzip_call = [utils.resolve_executable("gunzip"), source_file]
        gunzip = Popen(gunzip_call, stdout=PIPE, stderr=PIPE, cwd=workdir)
        logger.debug("gunzip call:{}".format(tar_call))
        gunzip_stream_data = gunzip.communicate()
        if gunzip.returncode is not 0:
            logger.error("{}".format(gunzip_stream_data))
            logger.error("gunzip returncode {}".format(gunzip.returncode))
            logger.error("gunzip stdout: {}\nstderr: {}".format(gunzip_stream_data))
            exit(1)
        else:
            logger.info("Gunzip of reference DB successful.")
    else:
        logger.error("Don't know what to do with {}, it does not look like a (gzipped) tar file".format(source_file))
        exit(1)

    return destination


def gunzip_copy(source_file, destination, logger):
    """
    Takes a source file and a destination and determines whether to 
    gunzip the file before moving it to the destination.
    """

    if source_file.lower().endswith((".gz")):
        logger.info("File %s seems gzipped, uncompressing to node...", source_file)
        
        # Remove the .gz suffix and redirect stdout to this file
        destination = destination[:-3]
        outfile = open(destination, "w")

        gunzip_call = [utils.resolve_executable("gunzip"), source_file, "-c"]
        gunzip = Popen(gunzip_call, stdout=outfile, stderr=PIPE).communicate()

        outfile.close()
        if gunzip[1] != "":
            logger.error("Could not gunzip %s to node", source_file)
            logger.error("Gunzip stderr: %s", gunzip[1])
            exit(1)
        else:
            logger.info("Successfully gunzipped %s to node.", source_file)
    else: # It is probably not compressed (at least not with gzip)
        try:
            logger.info("Copying %s to node...", source_file)
            shutil.copy(source_file, destination)
            logger.info("Successfully copied %s to node.", source_file)
        except OSError, message:
            logger.error("File copy error: %s", message)

    return destination 


def uncompress_into_Popen(filename, logger):
    """
    Determine filetype based on file name ending and start a Popen 
    object with gunzip stream output, otherwise cat into a pipe.
    """
    
    if filename.lower().endswith((".gz")):
        logger.info("File %s seems gzipped, uncompressing.", filename)
        gunzip_call = [utils.resolve_executable("gunzip"), "-c", filename]
        uncompressed_data = Popen(gunzip_call, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    else:
        logger.info("File %s does not seem gzipped.", filename)
        cat_call = [utils.resolve_executable("cat"), filename]
        uncompressed_data = Popen(cat_call, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    return uncompressed_data


def create_new_pipe(firstchar, source, logger):
    """
    Creates a new source pipe from a string and a Popen object.
    Inserts firstchar into the new stream and then appends the content
    of source via external program 'cat'.
    """

    new_source = Popen([r"(printf '\x%02x' && cat)" % ord(firstchar)], 
                       shell=True, stdin=source.stdout, stdout=PIPE)
    return new_source


def determine_format(source, logger):
    """
    Reads the first byte of the stream to determine file format
    (FASTA or FASTQ) and returns a new pipe with the data along
    with a format description (True for FASTQ, False for FASTA).
    """

    firstchar = source.stdout.read(1)
    if firstchar == "@":
        logger.info("Reads appear to be in FASTQ format.")
        fastq = True
        new_source = create_new_pipe(firstchar, source, logger)
    elif firstchar == ">":
        logger.info("Reads appear to be in FASTA format, cannot perform quality control.")
        fastq = False
        new_source = create_new_pipe(firstchar, source, logger)
    else:
        logger.error("Reads file not in FASTQ or FASTA format")
        exit(1)

    return (new_source, fastq)


def filtered_call(logger, source, program, **options):
    """
    Generic filter call.
    Calls PROGRAM with OPTIONS given as keyword arguments to this function
    which are supplied as command line options to the PROGRAM.
    The function assumes the PROGRAM takes the SOURCE as input on stdin
    and returns its output on stdout.
    """

    filter_call = [utils.resolve_executable(program)]
    args = [str(key)+str(option) for key, option in options.iteritems()]
    filter_call.extend(args)

    logger.debug("{} call: {}".format(program, ' '.join(filter_call)))
    result = Popen(filter_call, stdin=source.stdout, stdout=PIPE, stderr=PIPE)
    return result


def write_reads(source, destination, logger):
    """
    Takes a Popen object and writes its content to file.
    """

    # TODO: Create a thread that writes the source.stdout to a file instead.
    logger.info("Writing reads to local file {}...".format(destination))
    destination_file = open(destination, "w")
    write = Popen([utils.resolve_executable("cat")], stdin=source.stdout, stdout=destination_file)
    return write
    

        

def filter_human_reads_bowtie2(reads, options, logger):
    """
    Runs bowtie2 to filter out reads that DO NOT map to the given reference.
    """

    output_filename = reads+".filtered.fq"
    if not options.bowtie2FilterDB:
        log.error("--bowtie2FilterDB is empty! Sorry for noticing so late! :(")
        exit(1)

    db_name = os.path.basename(options.bowtie2FilterDB.split(".")[0])
    mapper_call = [utils.resolve_executable("bowtie2"),
                   "-x", db_name,
                   "-U", reads, 
                   "-S", "/dev/null", #output_filename,
                   "--un", output_filename,
                   "-p", str(options.bowtie2Threads)]

    # Run the command in the result dir and give the file_name relative to that.
    result_base = os.path.dirname(output_filename)
    # Run Bowtie2
    logger.info("Running bowtie2 to filter reads before mapping...")
    logger.debug("bowtie2 call: {0}".format(' '.join(mapper_call)))
    stdout.flush() # Force printout so users knows what's going on
    bowtie2 = Popen(mapper_call, stdout=PIPE, stderr=PIPE, cwd=result_base)
    bowtie2_stream_data = bowtie2.communicate()
    if bowtie2.returncode is not 0:
        logger.error("bowtie2: return code {}".format(bowtie2.returncode))
        logger.error("bowtie2: stdout: {}".format(bowtie2_stream_data[0])) 
        logger.error("bowtie2: stderr: {}".format(bowtie2_stream_data[1])) 
        exit(1)
    else:
        # TODO: assert mapping results?
        pass
    logger.debug("bowtie2: stdout: {}".format(bowtie2_stream_data[0])) 
    logger.debug("bowtie2: stderr: {}".format(bowtie2_stream_data[1])) 

    return output_filename




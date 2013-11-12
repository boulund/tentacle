#!/usr/bin/env python2.7
# Fredrik Boulund 2013
# Anders Sjogren 2013

from sys import exit, stdout
from subprocess import PIPE#, Popen
from collections import namedtuple
from time import time
import argparse
import os
import shutil
import tempfile

from gevent.subprocess import Popen
#import gevent
#gevent.monkey.patch_subprocess()
import psutil

import parseModule
from .. import utils

#InFiles = namedtuple("InFiles", ["contigs", "reads", "annotations"])
AllFiles = namedtuple("AllFiles", ["contigs", "reads", "annotations", "annotationStats", "log"])

class TentacleCore:
    def __init__(self, logger):
        self.logger = logger

    def copy_untar_ref_db(self, source_file, destination):
        """
        Copies and uncompresses gzipped tar file containing reference database to destination.
        """

        workdir = os.path.dirname(destination)

        if source_file.lower().endswith((".tar.gz", ".tar", ".tgz")):
            self.logger.info("It appears reference DB '%s' is in tar/gz format", source_file)
            self.logger.info("Extracting (and if necessary gunzipping) database...")
            shutil.copy(source_file, destination)
            tar_call = [utils.resolve_executable("tar"), "-xf", source_file]
            tar = Popen(tar_call, stdout=PIPE, stderr=PIPE, cwd=workdir)
            self.logger.debug("tar call:{}".format(tar_call))
            tar_stream_data = tar.communicate()
            if tar.returncode is not 0:
                self.logger.error("{}".format(tar_stream_data))
                self.logger.error("tar returncode {}".format(tar.returncode))
                self.logger.error("tar stdout: {}\nstderr: {}".format(tar_stream_data))
                exit(1)
            else:
                self.logger.info("Untar of reference DB successful.")
        elif source_file.lower().endswith((".gz")):
            self.logger.info("It appears reference DB '%s' is in gz format", source_file)
            self.logger.info("Gunzipping databsae...")
            shutil.copy(source_file, destination)
            gunzip_call = [utils.resolve_executable("gunzip"), source_file]
            gunzip = Popen(gunzip_call, stdout=PIPE, stderr=PIPE, cwd=workdir)
            self.logger.debug("gunzip call:{}".format(tar_call))
            gunzip_stream_data = gunzip.communicate()
            if gunzip.returncode is not 0:
                self.logger.error("{}".format(gunzip_stream_data))
                self.logger.error("gunzip returncode {}".format(gunzip.returncode))
                self.logger.error("gunzip stdout: {}\nstderr: {}".format(gunzip_stream_data))
                exit(1)
            else:
                self.logger.info("Gunzip of reference DB successful.")
        else:
            self.logger.error("Don't know what to do with {}, it does not look like a (gzipped) tar file".format(source_file))
            exit(1)

        return destination


    def gunzip_copy(self, source_file, destination):
        """
        Takes a source file and a destination and determines whether to 
        gunzip the file before moving it to the destination.
        """
    
        if source_file.lower().endswith((".gz")):
            self.logger.info("File %s seems gzipped, uncompressing to node...", source_file)
            
            # Remove the .gz suffix and redirect stdout to this file
            destination = destination[:-3]
            outfile = open(destination, "w")
    
            gunzip_call = [utils.resolve_executable("gunzip"), source_file, "-c"]
            gunzip = Popen(gunzip_call, stdout=outfile, stderr=PIPE).communicate()
    
            outfile.close()
            if gunzip[1] != "":
                self.logger.error("Could not gunzip %s to node", source_file)
                self.logger.error("Gunzip stderr: %s", gunzip[1])
                exit(1)
            else:
                self.logger.info("Successfully gunzipped %s to node.", source_file)
        else: # It is probably not compressed (at least not with gzip)
            try:
                self.logger.info("Copying %s to node...", source_file)
                shutil.copy(source_file, destination)
                self.logger.info("Successfully copied %s to node.", source_file)
            except OSError, message:
                self.logger.error("File copy error: %s", message)
    
        return destination 
    
    
    def uncompress_into_Popen(self, filename):
        """
        Determine filetype based on file name ending and start a Popen 
        object with gunzip stream output, otherwise cat into a pipe.
        """
        
        if filename.lower().endswith((".gz")):
            self.logger.info("File %s seems gzipped, uncompressing.", filename)
            gunzip_call = [utils.resolve_executable("gunzip"), "-c", filename]
            uncompressed_data = Popen(gunzip_call, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        else:
            self.logger.info("File %s does not seem gzipped.", filename)
            cat_call = [utils.resolve_executable("cat"), filename]
            uncompressed_data = Popen(cat_call, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        return uncompressed_data
    
    
    def create_new_pipe(self, firstchar, source):
        """
        Creates a new source pipe from a string and a Popen object.
        Inserts firstchar into the new stream and then appends the content
        of source via external program 'cat'.
        """
    
        new_source = Popen([r"(printf '\x%02x' && cat)" % ord(firstchar)], 
                           shell=True, stdin=source.stdout, stdout=PIPE)
        return new_source
    
    
    def determine_format(self, source):
        """
        Reads the first byte of the stream to determine file format
        (FASTA or FASTQ) and returns a new pipe with the data along
        with a format description (True for FASTQ, False for FASTA).
        """
    
        firstchar = source.stdout.read(1)
        if firstchar == "@":
            self.logger.info("Reads appear to be in FASTQ format.")
            fastq = True
            new_source = self.create_new_pipe(firstchar, source)
        elif firstchar == ">":
            self.logger.info("Reads appear to be in FASTA format, cannot perform quality control.")
            fastq = False
            new_source = self.create_new_pipe(firstchar, source)
        else:
            self.logger.error("Reads file not in FASTQ or FASTA format")
            exit(1)
    
        return (new_source, fastq)
    
    
    def filtered_call(self, source, program, **options):
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
    
        self.logger.debug("{} call: {}".format(program, ' '.join(filter_call)))
        result = Popen(filter_call, stdin=source.stdout, stdout=PIPE, stderr=PIPE)
        return result
    
    
    def write_reads(self, source, destination):
        """
        Takes a Popen object and writes its content to file.
        """
    
        # TODO: Create a thread that writes the source.stdout to a file
        # instead.
        destination_file = open(destination, "w")
        write = Popen([utils.resolve_executable("cat")], stdin=source.stdout, stdout=destination_file)
        return write
    

        
    def prepare_reads(self, reads, destination, options):
        """
        Takes a set of reads and prepares them for mapping on the node.
        """
    
        # Make sure any .gz filename endings get removed from the destination
        # since some mapping tools rely on file endings to determine the
        # input format
        if destination.lower().endswith((".gz")):
            destination = destination[:-3]
    
        self.logger.info("Preparing %s for mapping.", reads)
    
        # Uncompress reads into Popen PIPE object
        uncompressed_reads = self.uncompress_into_Popen(reads)
    
        # Determine reads format (FASTA or FASTQ) and return new source stream
        read_source, fastq_format = self.determine_format(uncompressed_reads)
    
        # Perform filtering and trimming if FASTQ, 
        # otherwise just write to disk
        if fastq_format and not options.noQualityControl:
            self.logger.info("Performing quality control on reads...")
            self.logger.info("Filtering reads...")
            filtered_reads = self.filtered_call(source=read_source, 
                                    program="fastq_quality_filter",
                                    **{"-q":options.fastqMinQ, 
                                       "-p":options.fastqProportion,
                                       "-v":""})
            self.logger.info("Trimming reads...")
            trimmed_reads = self.filtered_call(source=filtered_reads,
                                   program="fastq_quality_trimmer",
                                   **{"-t":options.fastqThreshold,
                                      "-l":options.fastqMinLength,
                                      "-v":""})
            if options.pblat or options.blast or options.usearch:
                self.logger.info("Converting FASTQ to FASTA...")
                fasta_reads = self.filtered_call(source=trimmed_reads,
                                     program="fastq_to_fasta",
                                     **{"-n":"", #discards low quality reads
                                        "-v":""})
                self.logger.info("Writing filtered and trimmed reads to local storage...")
                # Append .fasta to filename since it is converted to that format
                # and pblat requires that suffix
                destination = destination+".fasta"
                written_reads = self.write_reads(fasta_reads, destination)
            else:
                self.logger.info("Writing filtered and trimmed reads to local storage...")
                written_reads = self.write_reads(trimmed_reads, destination)
            # Calling .communicate() on the Popen object runs the
            # entire pipeline that has been pending
            written_reads.communicate() # Writes to disk
            # TODO: Check returncodes of all parts of the pipeline
            self.logger.info("Read quality control and FASTA conversion completed.")
            self.logger.info("Filtering statistics:\n%s", filtered_reads.stderr.read())
            self.logger.info("Trimming statistics:\n%s", trimmed_reads.stderr.read())
            if options.pblat: self.logger.info("FASTA conversion statistics:\n%s", fasta_reads.stderr.read())
        else:
            if options.noQualityControl:
                self.logger.info("Skipping quality control and writing reads to local storage...")
            else:
                self.logger.info("Writing reads to local storage...")
            written_reads = self.write_reads(read_source, destination)
            # Calling .communicate() on the Popen object runs the
            # entire pipeline that has been pending
            written_reads.communicate() # Writes to disk
            self.logger.info("Successfully wrote reads to local disk.")

        if options.bowtie2FilterReads:
            # Transfer genome index for bowtie2 and perform read filtering
            db_destination = os.path.dirname(destination)+"/"+os.path.basename(options.bowtie2FilterDB)
            self.copy_untar_ref_db(options.bowtie2FilterDB, db_destination)
            filtered_reads = self.filter_human_reads_bowtie2(destination, options)
            self.logger.info("Finished preparing %s for mapping.", reads)
            return filtered_reads
    
        self.logger.info("Finished preparing %s for mapping.", reads)
        return destination


    def filter_human_reads_bowtie2(self, reads, options):
        """
        Runs bowtie2 to filter out reads that DO NOT map to the given reference.
        """

        output_filename = reads+".filtered.fq"
        if not options.bowtie2FilterDB:
            self.log.error("--bowtie2FilterDB is empty! Sorry for noticing so late! :(")
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
        self.logger.info("Running bowtie2 to filter reads before mapping...")
        self.logger.debug("bowtie2 call: {0}".format(' '.join(mapper_call)))
        stdout.flush() # Force printout so users knows what's going on
        bowtie2 = Popen(mapper_call, stdout=PIPE, stderr=PIPE, cwd=result_base)
        bowtie2_stream_data = bowtie2.communicate()
        if bowtie2.returncode is not 0:
            self.logger.error("bowtie2: return code {}".format(bowtie2.returncode))
            self.logger.error("bowtie2: stdout: {}".format(bowtie2_stream_data[0])) 
            self.logger.error("bowtie2: stderr: {}".format(bowtie2_stream_data[1])) 
            exit(1)
        else:
            # TODO: assert mapping results?
            pass
        self.logger.debug("bowtie2: stdout: {}".format(bowtie2_stream_data[0])) 
        self.logger.debug("bowtie2: stderr: {}".format(bowtie2_stream_data[1])) 

        return output_filename



    def run_pblat(self, local, options):
        """
        Runs pblat
        """

        mapper_call = [utils.resolve_executable("pblat"),
                       "-threads=" + str(options.pblatThreads),
                       "-out=blast8" ]
        
        # A workaround for pblat not working correctly with some absolute path 
        # names for the result:
        # Run the command in the result dir and give the file name relative to that.
        output_filename = local.reads+".results"
        result_base = os.path.dirname(output_filename)

        # Append arguments to mapper_call
        mapper_call.append(os.path.relpath(local.contigs, result_base))
        mapper_call.append(os.path.relpath(local.reads, result_base))
        mapper_call.append(os.path.relpath(output_filename, result_base))

        # Run pblat
        self.logger.info("Running pblat...")
        self.logger.debug("pblat call: {0}".format(' '.join(mapper_call)))
        stdout.flush() # Force printout so user knows what's going on
        pblat = Popen(mapper_call, stdout=PIPE, stderr=PIPE, cwd=result_base)
        pblat_stream_data = pblat.communicate()
        if pblat.returncode is not 0:
            self.logger.error("pblat: return code {}".format(pblat.returncode))
            self.logger.error("pblat: stdout: {}".format(pblat_stream_data[0]))
            self.logger.error("pblat: stderr: {}".format(pblat_stream_data[1]))
            exit(1)
        else:
            # assert_mapping_results()
            pass
        self.logger.debug("pblat: stdout: {}".format(pblat_stream_data[0]))
        self.logger.debug("pblat: stderr: {}".format(pblat_stream_data[1]))

        return output_filename


    def run_blast(self, local, options):
        """
        Runs NCBI blast
        """

        output_filename = local.reads+".results"
        mapper_call = [utils.resolve_executable(options.blastProgram),
                       "-outfmt", "6", # blast8 tabular output format
                       "-query", str(local.reads),
                       "-db", options.blastDBName.split(".", 1)[0], 
                       "-out", output_filename, # Output written to here!
                       "-num_threads", str(options.blastThreads)]

        if options.blastTask:
            mapper_call.append("-task")
            mapper_call.append(str(options.blastTask))
        # Run the command in the result dir and give the file_name relative to that.
        result_base = os.path.dirname(output_filename)
        # Run BLAST
        self.logger.info("Running BLAST...")
        self.logger.debug("blast call: {0}".format(' '.join(mapper_call)))
        stdout.flush() # Force printout so users knows what's going on
        blast = Popen(mapper_call, stdout=PIPE, stderr=PIPE, cwd=result_base)
        blast_stream_data = blast.communicate()
        if blast.returncode is not 0:
            self.logger.error("blast: return code {}".format(blast.returncode))
            self.logger.error("blast: stdout: {}".format(blast_stream_data[0])) 
            self.logger.error("blast: stderr: {}".format(blast_stream_data[1])) 
            exit(1)
        else:
            # TODO: assert mapping results?
            pass
        self.logger.debug("blast: stdout: {}".format(blast_stream_data[0])) 
        self.logger.debug("blast: stderr: {}".format(blast_stream_data[1])) 

        return output_filename


    def run_usearch(self, local, options):
        """
        Runs USEARCH
        """

        output_filename = local.reads+".results"
        mapper_call = [utils.resolve_executable("usearch"),
                       "-usearch_global", str(local.reads),
                       "-db", options.usearchDBName.split(".", 1)[0]+".udb",
                       "-query_cov", str(options.usearchQueryCov),
                       "-blast6out", output_filename]

        if options.usearchQueryCov:
            mapper_call.append("-id")
            mapper_call.append(str(options.usearchID))
        # Run the command in the result dir and give the file_name relative to that.
        result_base = os.path.dirname(output_filename)
        # Run USEARCH
        self.logger.info("Running USEARCH...")
        self.logger.debug("usearch call: {0}".format(' '.join(mapper_call)))
        stdout.flush() # Force printout so users knows what's going on
        usearch = Popen(mapper_call, stdout=PIPE, stderr=PIPE, cwd=result_base)
        usearch_stream_data = usearch.communicate()
        if usearch.returncode is not 0:
            self.logger.error("usearch: return code {}".format(usearch.returncode))
            self.logger.error("usearch: stdout: {}".format(usearch_stream_data[0])) 
            self.logger.error("usearch: stderr: {}".format(usearch_stream_data[1])) 
            exit(1)
        else:
            # TODO: assert mapping results?
            pass
        self.logger.debug("usearch: stdout: {}".format(usearch_stream_data[0])) 
        self.logger.debug("usearch: stderr: {}".format(usearch_stream_data[1])) 

        return output_filename


    def run_bowtie2(self, local, options):
        """
        Runs bowtie2
        """

        output_filename = local.reads+".results"
        mapper_call = [utils.resolve_executable("bowtie2"),
                       "-x", str(options.bowtie2DBName),
                       "-S", output_filename,
                       "-U", local.reads, 
                       "-p", str(options.bowtie2Threads)]

        # Run the command in the result dir and give the file_name relative to that.
        result_base = os.path.dirname(output_filename)
        # Run Bowtie2
        self.logger.info("Running bowtie2...")
        self.logger.debug("bowtie2 call: {0}".format(' '.join(mapper_call)))
        stdout.flush() # Force printout so users knows what's going on
        bowtie2 = Popen(mapper_call, stdout=PIPE, stderr=PIPE, cwd=result_base)
        bowtie2_stream_data = bowtie2.communicate()
        if bowtie2.returncode is not 0:
            self.logger.error("bowtie2: return code {}".format(bowtie2.returncode))
            self.logger.error("bowtie2: stdout: {}".format(bowtie2_stream_data[0])) 
            self.logger.error("bowtie2: stderr: {}".format(bowtie2_stream_data[1])) 
            exit(1)
        else:
            # TODO: assert mapping results?
            pass
        self.logger.debug("bowtie2: stdout: {}".format(bowtie2_stream_data[0])) 
        self.logger.debug("bowtie2: stderr: {}".format(bowtie2_stream_data[1])) 

        return output_filename


    def run_gem(self, local, options):
        """
        Runs GEM
        """
        mapper_call = [utils.resolve_executable("gem-mapper"),
                       "-I", str(options.gemDBName)+".gem",
                       "-i", local.reads, 
                       "-o", local.reads, #output prefix; gem appends with .map
                       "-T", str(options.gemThreads),
                       "-m", str(options.gemm),
                       "-e", str(options.geme),
                       "--min-matched-bases", str(options.gemMinMatchedBases),
                       "--granularity", str(options.gemGranularity)
                       ]

        if not options.gemFasta:
            mapper_call.append("-q")
            mapper_call.append('ignore')

        output_filename = local.reads+".map"
        # Run the command in the result dir and give the file_name relative to that.
        result_base = os.path.dirname(output_filename)
        # Run GEM
        self.logger.info("Running gem...")
        self.logger.debug("gem call: {0}".format(' '.join(mapper_call)))
        stdout.flush() # Force printout so users knows what's going on
        gem = Popen(mapper_call, stdout=PIPE, stderr=PIPE, cwd=result_base)
        gem_stream_data = gem.communicate()
        if gem.returncode is not 0:
            self.logger.error("gem: return code {}".format(gem.returncode))
            self.logger.error("gem: stdout: {}".format(gem_stream_data[0])) 
            self.logger.error("gem: stderr: {}".format(gem_stream_data[1])) 
            exit(1)
        else:
            # TODO: assert mapping results?
            pass
        self.logger.debug("gem: stdout: {}".format(gem_stream_data[0])) 
        self.logger.debug("gem: stderr: {}".format(gem_stream_data[1])) 

        return output_filename


    def run_razers3(self, local, options):
        """
        Run RazerS3
        """
        mapper_call = [utils.resolve_executable("razers3"),
                       "-i", str(options.razers3Identity),
                       "-rr", str(options.razers3Recognition), 
                       "-m", str(options.razers3Max)]
        if options.razers3Swift:
            mapper_call.append("-fl")
            mapper_call.append("swift")
        # Append arguments to mapper_call
        mapper_call.append(local.contigs)
        mapper_call.append(local.reads)

        # Run RazerS3
        self.logger.info("Running RazerS3...")
        self.logger.debug("RazerS3 call: %s", ' '.join(mapper_call))
        stdout.flush() # Force printout so user knows what's going on
        razers3 = Popen(mapper_call, stdout=PIPE, stderr=PIPE)
        razers3_stream_data = razers3.communicate()
        if razers3.returncode is not 0:
            self.logger.error("RazerS3 return code: {}".format(razers3.returncode))
            self.logger.error("RazerS3 stdout: {}".format(razers3_stream_data[0]))
            self.logger.error("RazerS3 stderr: {}".format(razers3_stream_data[1]))
            exit(1)
        else:
            # TODO: Add some kind of control of results file size or 
            # contents to ensure mapping was actually successful?
            # An empty result file might be ok? 
            # Call function something like assert_mapping_results() ?
            self.logger.info("RazerS3 mapping completed.")
            if os.path.getsize(local.reads+".razers") == 0: 
                self.logger.warning("Mapping results are empty.")
            self.logger.debug("RazerS3 stdout:\n%s", razers3_stream_data[0])
            self.logger.debug("RazerS3 stderr:\n%s", razers3_stream_data[1])

        return local.reads+".razers"
    

    def preprocess_data_and_map_reads(self, files, options):
        """
        Performs file copy operations, gunzip, quality filtering etc. 
        before running the mapper.
        """
        
        preprocess_annotation_time = time()
        temp_dir = tempfile.mkdtemp()
        self.logger.info("Using created tempdir {} .".format(temp_dir))
    
        # Define local filenames of source files
        def rebase_to_local_tmp(f):
            return os.path.join(temp_dir, os.path.basename(f))
        LocalTuple = namedtuple("local", ["contigs", "reads", "annotations"])
        local = LocalTuple(rebase_to_local_tmp(files.contigs), rebase_to_local_tmp(files.reads), rebase_to_local_tmp(files.annotations))
    
        # Copy annotation file to node, returns updated local filename
        # TODO: This could be parallelized
        new_annotations = self.gunzip_copy(files.annotations, local.annotations)
        local = local._replace(annotations=new_annotations)
        self.logger.info("Time to transfer and prepare annotations: %s", time()-preprocess_annotation_time)

        # Blast, bowtie2 and GEM require a database to compare against,
        # filename given by the user should be a .tar.gz archive.
        preprocess_references_time = time()
        if options.blast: 
            self.copy_untar_ref_db(files.contigs, local.contigs)
            local = local._replace(contigs=rebase_to_local_tmp(options.blastDBName))
        elif options.usearch:
            self.copy_untar_ref_db(files.contigs, local.contigs)
            local = local._replace(contigs=rebase_to_local_tmp(options.usearchDBName))
        elif options.bowtie2:
            self.copy_untar_ref_db(files.contigs, local.contigs)
            local = local._replace(contigs=rebase_to_local_tmp(options.bowtie2DBName))
        elif options.gem:
            self.copy_untar_ref_db(files.contigs, local.contigs)
            local = local._replace(contigs=rebase_to_local_tmp(options.gemDBName))
        else:
            new_contigs = self.gunzip_copy(files.contigs, local.contigs)
            local = local._replace(contigs=new_contigs)
        self.logger.info("Time to transfer and prepare references: %s", time()-preprocess_references_time)
    
        # Prepare reads for mapping (gunzip, filter and transfer to node)
        # Returns updated local filename
        reads_time = time()
        new_reads = self.prepare_reads(files.reads, local.reads, options)
        local = local._replace(reads=new_reads)
        self.logger.info("Time to transfer and preprocess reads: %s", time()-reads_time)
        
        maptime = time()
        # TODO: Add mapper agnostic paired-end capabilities
        if options.pblat:
            mapped_reads_file_path = self.run_pblat(local, options)
        elif options.blast:
            mapped_reads_file_path = self.run_blast(local, options)
        elif options.bowtie2:
            mapped_reads_file_path = self.run_bowtie2(local, options)
        elif options.gem:
            mapped_reads_file_path = self.run_gem(local, options)
        elif options.razers3:
            mapped_reads_file_path = self.run_razers3(local, options)
        elif options.usearch:
            mapped_reads_file_path = self.run_usearch(local, options)
        else:
            self.logger.error("No mapper selected! (this should never happen!)")
            exit(1)
        self.logger.info("Time to map reads: %s", time()-maptime)

        # Prepare and return a named tuple with essential information from mapping
        MappedReadsTuple = namedtuple("mapped_reads", ["contigs", "mapped_reads", "annotations"])
        mapped_reads = MappedReadsTuple(local.contigs,
                                        mapped_reads_file_path, 
                                        local.annotations)
        return (mapped_reads, temp_dir)
    
    
    def analyse_coverage(self, mapped_reads, outfile, options):
        """
        Analyses mapped contigs and counts map coverage
        """
    
        # Perform analysis of contigs and initialize data structure
        self.logger.info("Initializing map coverage data structure...")
        contig_coverage = parseModule.indexContigs(mapped_reads.contigs, self.logger)
        self.logger.info("Map coverage data structure initialized.")
    
        # Sum the number of mapped contigs
        self.logger.info("Summing number of mapped contigs...")
        contig_coverage = parseModule.sumMapCounts(mapped_reads.mapped_reads, 
                                                   contig_coverage, 
                                                   options,
                                                   self.logger)
        self.logger.info("Number of mapped contigs summation completed.")
    
        # DEBUG printing (EXTREMELY SLOW)
        if options.outputCoverage:
            import numpy as np
            np.set_printoptions(threshold='nan', linewidth='inf')
            self.logger.debug("Writing complete coverage maps to contigCoverage.txt... (this is sloooow!)")
            with open("contigCoverage.txt", "w") as coverageFile:
                for contig in contig_coverage.keys():
                    coverageFile.write('\t'.join([contig, str(contig_coverage[contig])+"\n"]))
            self.logger.debug("Coverage maps written to contigCoverage.txt.")
    
        # Compute counts per annotation
        self.logger.info("Computing counts per annotation, writing to {}...".format(outfile))
        parseModule.computeAnnotationCounts(mapped_reads.annotations, contig_coverage, outfile, self.logger)
        self.logger.info("Counts per annotation computation completed.")


    def delete_temporary_files(self, temp_dir):
        """
        Deletes all temporary files created during analysis.
        """
        # TODO: More logic to determine if delete was actually successful etc.
        self.logger.info("Deleting temporary files in folder '{}'...".format(temp_dir))
        shutil.rmtree(temp_dir)


    def analyse(self, files, options):
        mapped_reads, temp_dir = self.preprocess_data_and_map_reads(files, options)
        coveragetime = time()
        self.analyse_coverage(mapped_reads, files.annotationStats, options)
        self.logger.info("Time to analyse coverage: %s", time()-coveragetime)
        self.logger.info("Results available in %s", files.annotationStats)
        if options.deleteTempFiles:
            self.delete_temporary_files(temp_dir)
        self.logger.info(" ----- ===== LOGGING COMPLETED ===== ----- ")
    
    
        
    @staticmethod
    def create_fastq_argparser():
        """
        Creates parser for FASTQ quality control options (filtering and trimming). 
        """
        
        parser = argparse.ArgumentParser(add_help=False)
        quality_filtering_group = parser.add_argument_group("Quality filtering options", "Options for FASTQ")
        #TODO: Change dest to be the same as argument, e.g. fastqMinQ=>fqMinQuality. Will be useful when writing out config file with all options for future use with @saved-opts as argument.
        quality_filtering_group.add_argument("--noQualityControl", dest="noQualityControl",
            action="store_true", default=False,
            help="FASTQ quality control: Do not perform quality filtering or trimming [default: %(default)s]")
        quality_filtering_group.add_argument("--fqMinQuality", dest="fastqMinQ", 
            type=int, default=10, 
            help="FASTQ filter: minimum base quality score, [default: %(default)s]")
        quality_filtering_group.add_argument("--fqProportion", dest="fastqProportion",
            type=int, default=50,
            help="FASTQ filter: minimum proportion of bases above base quality score [default: %(default)s]")
        quality_filtering_group.add_argument("--fqThreshold", dest="fastqThreshold",
            type=int, default=1, 
            help="FASTQ trim: minium quality threshold. Nucleotides with lower quality will be trimmed from the end of the sequence, [default: %(default)s]")
        quality_filtering_group.add_argument("--fqMinlength", dest="fastqMinLength",
            type=int, default=0,
            help="FASTQ trim: minimum length. Sequences shorter will be discarded [default: 0 (entire read)]")    
        return parser
    
    
    @staticmethod
    def create_razerS3_argparser():
        """
        Creates parser for RazerS3 options (used for mapping).
        """
    
        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options", "Options for Razers3.")
        mapping_group.add_argument("--razers3", dest="razers3",
            default=False, action="store_true",
            help="Perform mapping using RazerS3 [default %(default)s]")
        mapping_group.add_argument("--r3Identity", dest="razers3Identity",
            type=int, default=95,
            help="RazerS3: Percent identity of matched reads [default: %(default)s]")
        mapping_group.add_argument("--r3Recognition", dest="razers3Recognition",
            type=int, default=100,
            help="RazerS3: Recognition rate (sensitivity) [default: %(default)s]")
        mapping_group.add_argument("--r3Max", dest="razers3Max",
            type=int, default=1,
            help="RazerS3: Max number of returned matches per read [default: %(default)s]")
        mapping_group.add_argument("--r3Swift", dest="razers3Swift", action="store_true", 
            default=False,
            help="RazerS3: Change RazerS3 from pigeonhole to swift filter. [default: pigeonhole]")
        # TODO: Remake the implementation of paired end data to make it mapper agnostic.
        #mapping_group.add_argument("--r3Paired", dest="razers3Paired",
        #    type=str, default=False,
        #    help="RazerS3: Paired end reads file [default: not used]")
        return parser
    

    @staticmethod
    def create_blast_argparser():
        """
        Creates parser for blast options (used for mapping).
        """
    
        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options", "Options for blast.")
        mapping_group.add_argument("--blast", dest="blast",
            default=False, action="store_true",
            help="blast: Perform mapping using blast [default: %(default)s]")
        mapping_group.add_argument("--blastProgram", dest="blastProgram",
            type=str, default="blastn", metavar="PROGNAME",
            help="blast: Set what blast program to use [default: %(default)s]")
        mapping_group.add_argument("--blastThreads", dest="blastThreads",
            default=psutil.NUM_CPUS, type=int, metavar="N",
            help="blast: number of threads allowed [default: %(default)s]")
        mapping_group.add_argument("--blastTask", dest="blastTask",
            default="", type=str,
            help="blast: What task to be run, refer to blast manual for available options [default: %(default)s]")
        mapping_group.add_argument("--blastDBName", dest="blastDBName",
            type=str, default="", metavar="DBNAME",
            help="blast: Name of the FASTA file in the database tarball (including extension). It must have the same basename as the rest of the DB.")
        return parser
    

    @staticmethod
    def create_bowtie2_argparser():
        """
        Creates parser for bowtie2 options (used for mapping).
        """
    
        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options", "Options for bowtie2.")
        mapping_group.add_argument("--bowtie2", dest="bowtie2",
            default=False, action="store_true",
            help="bowtie2: Perform mapping using bowtie2 [default: %(default)s]")
        mapping_group.add_argument("--bowtie2Fasta", dest="bowtie2Fasta",
            default=False, action="store_true",
            help="bowtie2: Input files are FASTA format and not FASTQ [default %(default)s].")
        mapping_group.add_argument("--bowtie2Threads", dest="bowtie2Threads",
            default=psutil.NUM_CPUS, type=int, metavar="N",
            help="bowtie2: number of threads allowed [default: %(default)s]")
        mapping_group.add_argument("--bowtie2DBName", dest="bowtie2DBName",
            type=str, default="", metavar="DBNAME",
            help="bowtie2: Name of the reference file BASENAME in the database tarball (NO extension). It must have the same basename as the rest of the DB.")
        mapping_group.add_argument("--bowtie2FilterReads", dest="bowtie2FilterReads",
            action="store_true", 
            help="bowtie2: Use bowtie2 to filter out for example human reads in the read preprocessing step [default: %(default)s].")
        mapping_group.add_argument("--bowtie2FilterDB", dest="bowtie2FilterDB",
            type=str, default="", metavar="FilterDB", 
            help="bowtie2: Name of the filtering reference database tarball (including extension). It must have the same basename as the rest of the actual DB files.")
        return parser


    @staticmethod
    def create_gem_argparser():
        """
        Creates parser for GEM options (used for mapping).
        """
    
        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options", "Options for GEM.")
        mapping_group.add_argument("--gem", dest="gem",
            default=False, action="store_true",
            help="GEM: Perform mapping using GEM [default: %(default)s]")
        mapping_group.add_argument("--gemFasta", dest="gemFasta",
            default=False, action="store_true",
            help="GEM: Input files are FASTA format and not FASTQ [default %(default)s].")
        mapping_group.add_argument("--gemThreads", dest="gemThreads",
            default=psutil.NUM_CPUS, type=int, metavar="N",
            help="GEM: number of threads allowed [default: %(default)s (autodetected)]")
        mapping_group.add_argument("--gemDBName", dest="gemDBName",
            type=str, default="", metavar="DBNAME",
            help="GEM: Name of the reference file in the database tarball (i.e. entire name of FASTA file). It must have the same basename as the rest of the DB.")
        mapping_group.add_argument("--gemm", dest="gemm",
            type=float, default=0.04, metavar="m", 
            help="GEM: max_mismatches, percent mismatches [default: %(default)s]")
        mapping_group.add_argument("--geme", dest="geme",
            type=float, default=0.04, metavar="e", 
            help="GEM: max_exit_distance, percent differences [default: %(default)s]")
        mapping_group.add_argument("--gemMinMatchedBases", dest="gemMinMatchedBases",
            type=float, default=0.80, metavar="B", 
            help="GEM: min-matched-bases, percent [default: %(default)s]")
        mapping_group.add_argument("--gemGranularity", dest="gemGranularity",
            type=int, default=2500000, metavar="G", 
            help="GEM: granularity when reading from file (in bytes) [default: %(default)s]")
        return parser


    @staticmethod
    def create_pblat_argparser():
        """
        Creates parser for pblat options (used for mapping).
        """
    
        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options", "Options for pblat.")
        mapping_group.add_argument("--pblat", dest="pblat",
            default=False, action="store_true",
            help="pblat: Perform mapping using pblat [default: %(default)s]")
        mapping_group.add_argument("--pblatThreads", dest="pblatThreads",
            type=int, default=psutil.NUM_CPUS, metavar="N",
            help="pblat: Set number of threads for parallel blat mapping [default: N=%(default)s [=the current number of CPUs]]")
        return parser


    @staticmethod
    def create_usearch_argparser():
        """
        Creates parser for usearch options (used for mapping).
        """
    
        parser = argparse.ArgumentParser(add_help=False)
        mapping_group = parser.add_argument_group("Mapping options", "Options for usearch.")
        mapping_group.add_argument("--usearch", dest="usearch",
            default=False, action="store_true",
            help="usearch: Perform mapping using usearch [default: %(default)s]")
        mapping_group.add_argument("--usearchID", dest="usearchID",
            type=float, default="0.9", metavar="I",
            help="usearch: Sequence similarity for usearch_global [default: %(default)s]")
        mapping_group.add_argument("--usearchQueryCov", dest="usearchQueryCov",
            type=str, default="", metavar="COVERAGE",
            help="usearch: Query coverage in range 0.0-1.0.")
        mapping_group.add_argument("--usearchDBName", dest="usearchDBName",
            type=str, default="", metavar="DBNAME",
            help="usearch: Name of the FASTA file in the database tarball (including extension). It must have the same basename as the rest of the DB.")
        return parser
    
    
    @staticmethod
    def create_processing_argarser():
        """
        Creates parser for options that describes HOW to process the files (not WHAT files are to be processed).
        
        Is used both for the single contig-file and many-contig-files cases.
        """
        
        parser = argparse.ArgumentParser(parents=[TentacleCore.create_fastq_argparser(), 
                                                  TentacleCore.create_razerS3_argparser(),
                                                  TentacleCore.create_pblat_argparser(),
                                                  TentacleCore.create_blast_argparser(),
                                                  TentacleCore.create_bowtie2_argparser(),
                                                  TentacleCore.create_gem_argparser(),
                                                  TentacleCore.create_usearch_argparser()], add_help=False)
     
        debug_group = parser.add_argument_group("DEBUG developer options", "Use with caution!")
        debug_group.add_argument("--outputCoverage", dest="outputCoverage", action="store_true", default=False,
            help="Outputs complete coverage information into contigCoverage.txt")
            
        return parser
    
        
    @staticmethod
    def extract_file_options(options):
        # Define original source files
        # Simple quick validity check of positional arguments.
        # No check for actual validity of content here, 
        # mappers will crash later if they are malformed.
        utils.assert_file_exists("contigs", options.contigs);
        utils.assert_file_exists("reads", options.reads);
        utils.assert_file_exists("annotations", options.annotations);
        return AllFiles(options.contigs, options.reads, options.annotations, options.annotationStatsFile, options.logfile)
    
    
    @staticmethod
    def create_single_data_argparser():
        """
        Creates parser for all arguments for when a single triplet (contigs, reads, annotions) are to be processed.
        
        Performs some rudimental file existance assertions
        """
    
        parser = argparse.ArgumentParser(description="Maps reads to annotations in contigs and produces corresponding stats.", parents=[TentacleCore.create_processing_argarser()], add_help=True)
        
        parser.add_argument("contigs", help="path to contigs file (gzippped FASTQ)")
        parser.add_argument("reads", help="path to read file (gzipped FASTQ)")
        parser.add_argument("annotations", help="path to annotation file (tab separated text)")    
        #TODO: change default tentacle.log to something like reads_filename-extensions+".tab.log"?
        parser.add_argument("-l", "--logfile", dest="logfile", default="tentacle.log",
           help="Set a different log filename. [Default: %(default)s]")
        #TODO: change default annotationStats.tab to something like reads_filename-extensions+".tab"?
        #TODO: Make dest and option have same nomenclature (e.g. --annotationStatsFile, or rather dest="output", "-o" and "--output")
        parser.add_argument("-o", "--outAnnotationCounts", dest="annotationStatsFile", 
          default="annotationStats.tab",
          help="Output filename for the counts of reads that matched to annotations [default: %(default)s]")
            
        
        return parser
        
        
    @staticmethod
    def parse_args(argv):
        parser = TentacleCore.create_single_data_argparser()

        options = parser.parse_args()

        files = TentacleCore.extract_file_options(options)
    
        return (files, options)


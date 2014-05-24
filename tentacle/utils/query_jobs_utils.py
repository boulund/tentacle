#!/usr/bin/env python2.7
# coding: utf-8
# Fredrik Boulund
# Anders Sjögren
# 2014
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

from sys import argv, exit, path
from os.path import join, abspath, dirname
from datetime import datetime

def compute_runtime(start_time, end_time):
    """ Computes the time difference between two string representations of datetime objects."""
    time_format = "%Y-%m-%d %H:%M:%S.%f"
    stime = datetime.strptime(start_time, time_format)
    etime = datetime.strptime(end_time, time_format)
    return etime - stime

def write_jobs_summary(job_descriptions, filename):
    """ Writes status of all jobs in the list of currently registered jobs.

    The layout of job_descriptions is a tuple with two fields:
    The first field (job_descriptions[0]) contains a list of dictionaries.
    Each dictionary contains the following fields:
       description    A tuple containing the job basename and a tuple with 
                      fields for all files involved in the mapping job, e.g.:
                      ('name', (reference, reads, annotations, results_filename, log_filename))
       worker_name    string with the name of the worker    
       task           the task sent to the worker (a python function)
       result         gevent.event.AsyncResult
       start_time     string
       end_time       string
       attempts       list of tuples with attempt information: 
                      (worker_name, start_time, error_message)
    """
    with open(filename, "w") as file:
        file.write("{}: Listing {} jobs registered with the server.\n".format(datetime.now(), len(job_descriptions[0])))
        file.write("-------------------------------------------------------------------------------------\n")

        printouts = 0 
        for job in job_descriptions[0]:
            # Convenience
            basename = job["description"][0]
            attempts = job["attempts"]
            start_time = job["start_time"]
            end_time = job["end_time"]
            worker_name = job["worker_name"]
            result = job["result"]
            reads_file = job["description"][1][1] 

            jobinfo = [] 
            jobinfo.append("Job: {}".format(basename))
            jobinfo.append("  Filename: {}".format(reads_file))
            if start_time:
                jobinfo.append("  Started:   {}".format(start_time))
                if end_time:
                    jobinfo.append("  Completed: {}".format(end_time))
                    jobinfo.append("  Runtime:               {}".format(compute_runtime(start_time, end_time)))
                    jobinfo.append("  Completed by worker: {}.".format(worker_name))
                elif len(attempts) > 0:
                    jobinfo.append("  Incomplete. ERROR(S).")
                    jobinfo.append("  Retried {} times.".format(len(attempts)))
                else:
                    jobinfo.append("  Incomplete.")
                    jobinfo.append("  Run by {}.".format(worker_name))
            elif len(attempts) > 0:
                jobinfo.append("  Incomplete. ERROR(S).")
                jobinfo.append("  Retried {} times.".format(len(attempts)))
            else:
                jobinfo.append("  Not started.")

            jobinfo.append("\n") #The final newline after each job listing
            file.write('\n'.join(jobinfo))
            printouts+=1
        file.write("-------------------------------------------------------------------------------------\n")
        file.write("{}: Listed {} jobs\n".format(datetime.now(), printouts))

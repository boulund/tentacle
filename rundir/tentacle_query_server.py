#!/usr/bin/env python
# coding: utf-8
# Fredrik Boulund 
# Anders Sjögren

from zerorpc.exceptions import LostRemote
from sys import argv, exit, path
from os.path import join, abspath, dirname
import argparse
import re
from datetime import datetime

try:
    from tentacle.utils.zerorpc_utils import run_single_rpc
except ImportError:
    # If import fails Tentacle is probably not installed in 
    # python site-packages. Try to run it from the 
    # current directory instead.
    # Add TENTACLE_ROOT to PATH to be able to import Tentacle
    run_dir = abspath(dirname(__file__))
    base_dir = abspath(join(run_dir,".."))
    path.append(base_dir)
    try:
        from tentacle.utils.zerorpc_utils import run_single_rpc
    except ImportError:
        print "ERROR: Cannot import/find Tentacle, is it properly installed?"
        print "If you're trying to run Tentacle without installing, make sure to"
        print "run it from within the %TENTACLE_ROOT%/rundir directory."
        exit()


def parse_argv(argv):
    parser = argparse.ArgumentParser(description="Query a running Tentacle server for registered jobs.")
    parser.add_argument("address", metavar="ADDRESS", type=str, 
        help="The address of the Tentacle server to query, including tcp:// \
        prefix and port postfix (e.g. tcp://192.168.0.1:5150).")
    parser.add_argument("--display", type=str, default="all",
        choices=["all", "running", "completed", "incomplete", "errors"],
        help="Display either completed, incomplete, all, or only registerd jobs with errors.")
    parser.add_argument("--showfilenames", action="store_true",
        help="Display complete paths for read filenames in listings [default: %(default)s].")
    parser.add_argument("--max", metavar="N", type=int, default=False,
        help="Display a maximum of N listings. Useful to combine with 'errors' to reduce printout clutter\
        and aid debugging")
    parser.add_argument("--list", dest="re", metavar="REGEXP", type=str, default="",
        help="List only jobs with basenames that match REGEXP") 
    parser.add_argument("--interactive", action="store_true",
        help="Run the application in interactive mode, for easier interaction with the listings [default: %(default)s]")

    if len(argv) < 2:
        parser.print_help()
        exit()

    args = parser.parse_args()
    if not args.address.startswith("tcp://"):
        print "ERROR: Address needs tcp:// prefix"
    return parser.parse_args()


def compute_runtime(start_time, end_time):
    """ Computes the time difference between two string representations of datetime objects."""
    time_format = "%Y-%m-%d %H:%M:%S.%f"
    stime = datetime.strptime(start_time, time_format)
    etime = datetime.strptime(end_time, time_format)
    return etime - stime



def print_registered_jobs(options):
    """ Prints job registered at a Tentacle server running at ADDRESS.

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
    address = options.address
    display = options.display
    show_read_filenames = options.showfilenames
    max_printouts = options.max
    if options.re:
        regex = re.compile(options.re)

    try:
        job_descriptions = run_single_rpc([address], lambda registry:registry.get_mapped_jobs_description())
    except LostRemote:
        print "ERROR: Cannot connect to server at {}.\n".format(address)
        exit()
    try:
        number_of_registered_jobs = len(job_descriptions[0])
    except IndexError:
        print "ERROR: Got bad response from server at {}. Try again.\n".format(address)
        exit()

    print ""
    print "{}: Listing '{}' out of {} jobs currently registered \n\
                            at the server with address: {}.".format(datetime.now(), display, number_of_registered_jobs, address)
    if options.re:
        print "                            Filtering listing using regex: '{}'.".format(options.re)
    print "-------------------------------------------------------------------------------------"

    printouts = 0 
    for job in job_descriptions[0]:
        if max_printouts and printouts >= max_printouts:
            break

        # Convenience
        basename = job["description"][0]
        attempts = job["attempts"]
        start_time = job["start_time"]
        end_time = job["end_time"]
        worker_name = job["worker_name"]
        result = job["result"]
        if show_read_filenames:
            reads_file = job["description"][1][1] 
        else:
            reads_file = ""


        if options.re:
            match = re.search(regex, basename)
            if match is None:
                # Skip printing this job if the basename doesn't match regexp
                continue  

                       
        # Display logic for different listing options
        if "all" in display:
            print "Job:", basename, reads_file
            if start_time:
                print "  Started:   ", start_time
                if end_time:
                    print "  Completed: ", end_time
                    print "  Runtime:               ", compute_runtime(start_time, end_time)
                    print "  Completed by worker: {}.".format(worker_name)
                elif len(attempts) > 0:
                    print "  Incomplete. ERROR(S)."
                    print "  Retried {} times.".format(len(attempts))
                else:
                    print "  Incomplete."
                    print "  Run by {}.".format(worker_name)
            elif len(attempts) > 0:
                if start_time:
                    print "  Started:   ", start_time
                    print "  Run by {}.".format(worker_name)
                if len(attempts) > 0:
                    print "  Incomplete. ERROR(S)."
                    print "  Retried {} times.".format(len(attempts))
                else:
                    print "  Incomplete."
            else:
                print "  Not started."
            printouts+=1
        elif "running" in display:
            if start_time and not end_time:
                print "Job:", basename, reads_file
                print "  Started:   ", start_time
                print "  Incomplete."
                print "  Run by {}.".format(worker_name)
                printouts+=1
        elif "completed" in display:
            if bool(start_time and end_time):
                print "Job:", basename, reads_file
                print "  Started:   ", start_time
                print "  Completed: ", end_time 
                print "  Runtime:               ", compute_runtime(start_time, end_time)
                print "  Completed by worker: {}.".format(worker_name)
                printouts+=1
        elif "incomplete" in display:
            if "unset" in result:
                print "Job:", basename, reads_file
                if bool(start_time and end_time):
                    print "WARNING: This job is reported as completed but has no result set!"
                    print "  Started:   ", start_time
                    print "  Completed: ", end_time
                    print "  Runtime:               ", compute_runtime(start_time, end_time)
                    print "  Completed by worker: {}.".format(worker_name)
                elif start_time:
                    print "  Started:   ", start_time
                    if len(attempts) >= 1:
                        print "  Incomplete. ERROR(S)."
                    else:
                        print "  Incomplete."
                    if worker_name:
                        print "  Run by {}.".format(worker_name)
                else:
                    print "  Not started."
                    if len(attempts) >= 1:
                        print "  Incomplete. ERROR(S)."
                printouts+=1
        elif "errors" in display:
            if len(attempts) > 0:
                print "Job:", basename, reads_file
                print "  Attempted {} times with result(s):".format(len(attempts))
                for attempt in attempts:
                    worker_name, attempt_start_time, error_message = attempt
                    print "  Attempt at worker {}\n  at time {}.".format(worker_name, attempt_start_time)
                    print "  Received error message:\n", error_message
                printouts+=1
        else:
            break

            
            

    print "-------------------------------------------------------------------------------------"
    print "Finished listing {} jobs matching criteria '{}' out of {} registered jobs".format(printouts, display, len(job_descriptions[0]))
            

def wait_for_user_input(options):
    """ Read input from terminal """
    try:
        input = raw_input("""Enter one the following options to list jobs again:
 (a)ll, (r)unning, (c)ompleted, (i)ncomplete, (e)rrors, and press enter to display jobs again,
 (f)ilenames toggles read filename display,
 'n' changes the number of jobs listed: type e.g. 'n 2' to change number of listed jobs to two,
 'l' activates regexp filter: type e.g. 'l 100.*' to only list jobs that match the regexp '100.*',
 or type 'q' and press enter to quit.
Input: """)
        if input == "":
            return options
        elif input.lower().startswith("a"):
            options.display = "all"
        elif input.lower().startswith("r"):
            options.display = "running"
        elif input.lower().startswith("c"):
            options.display = "completed"
        elif input.lower().startswith("i"):
            options.display = "incomplete"
        elif input.lower().startswith("e"):
            options.display = "errors"
        elif input.lower().startswith("f"):
            options.showfilenames = not options.showfilenames
        elif input.lower().startswith("n"):
            try:
                options.max = int(input.split()[1])
            except ValueError:
                print "ERROR: Cannot parse max number of listings. Type e.g. 'n 4' to print the first 4 listings.'"
                return wait_for_user_input(options)
        elif input.lower().startswith("l"):
            try:
                options.re = input.split()[1]
            except ValueError:
                print "ERROR: Cannot parse regexp. Type e.g. 'l 100*' to only list jobs matching the regexp '100*'."
                return wait_for_user_input(options)
            except IndexError:
                print "ERROR: Cannot parse regexp. Type e.g. 'l 100*' to only list jobs matching the regexp '100*'."
                return wait_for_user_input(options)
        elif input.lower().startswith("q"):
            print "User exited."
            exit()
        else:
            print "ERROR: Option not recognized, try again or press Enter to use previous option."
            return wait_for_user_input(options)
        
        return options
    except KeyboardInterrupt:
        print "\nUser exited through Ctrl+C."
        exit()
    except EOFError:
        print "\nUser exited through Ctrl+D."
        exit()


if __name__ == "__main__":
    options = parse_argv(argv)
    if options.interactive:
        while True:
            print_registered_jobs(options)
            options = wait_for_user_input(options)
    else:
        print_registered_jobs(options)
        

"""Some utilities to interface to the slac batch system"""

import os

def dispatch_job(jobname, raft, run_num, logfile, **kwargs):
    """Stack the overscan region from all the amps on a sensor
    to look for coherent read noise

    Parameters
    ----------
    jobname:     str
       The command to send to the batch
    raft:        str
       The raft name, i.e., 'RTM-004-Dev'
    run_num:     str
       The run number, i.e,. '6106D'
    logfile:     str
       The path to the logfile


    Keyword arguments
    -----------------
    bsub_args:    str
    optstring:    str
    dry_run:      bool
    """
    bsub_args = kwargs.get('bsub_args', None)
    optstring = kwargs.get('optstring', None)
    dry_run = kwargs.get('dry_run', False)

    bsub_com = "bsub -o %s" % logfile
    if bsub_args is not None:
        bsub_com += " %s" % bsub_args

    bsub_com += " %s --raft %s --run %s" % (jobname, raft, run_num)

    if optstring is not None:
        bsub_com += " %s" % optstring

    if dry_run:
        print (bsub_com)
    else:
        os.system(bsub_com)


def read_runlist(filepath):
    """Read a list of runs from a txt file

    Parameters
    ----------
    filepath:     str

    Returns
    -------
    outlist:       list
       A list of tuples with (raft, run_num)
    """
    f = open(filepath)
    l = f.readline()

    outlist = []
    while l:
        tokens = l.split()
        if len(tokens) == 2:
            outlist.append(tokens)
        l = f.readline()
    return outlist

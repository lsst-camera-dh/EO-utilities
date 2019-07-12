"""This module contains functions dispatch analysis jobs.

Eventually it should be able to handle jobs by:

1) Running them on the same cpu as the parent job
2) Running them on a multiprocees pool
3) Running them on a batch farm

"""

from __future__ import with_statement

import os
import sys

from lsst.eo_utils.base.file_utils import makedir_safe
#import pipes

#from lsst.ctrl.pool import Batch, exportEnv, UMASK

def write_slurm_batchfile(jobname, logfile, **kwargs):
    """Dispatch a single job

    Parameters
    ----------
    jobname : `str`
        The command to run the job
    logfile : `str`
        The path to the logfile

    Keywords
    --------
    run : `str`
        The run number
    batch_args : `str`
        Arguments to pass to batch command
    optstring : `str`
        Additional arguments to pass to the command

    Returns
    -------
    batchfile : `str`
        The name of the slurm submission script file
    """
    run = kwargs.get('run', None)
    batch_args = kwargs.get('batch_args', None)
    optstring = kwargs.get('optstring', None)
    batchfile = os.path.join('sbatch', logfile.replace('.log', '.sl'))

    makedir_safe(batchfile)
    fout = open(batchfile, 'w')
    fout.write("#!/bin/bash -l\n")
    tokens = batch_args.split()
    for key, val in zip(tokens[0::2], tokens[1::2]):
        fout.write("#SBATCH %s %s\n" % (key, val))
    fout.write("\n")
    sub_com = "srun --output %s" % logfile

    if run is None:
        sub_com += " %s" % jobname
    else:
        sub_com += " %s --run %s" % (jobname, run)
    sub_com += " %s" % optstring

    fout.write("%s\n" % sub_com)
    fout.close()
    return batchfile



def dispatch_job(jobname, logfile, **kwargs):
    """Dispatch a single job

    Parameters
    ----------
    jobname : `str`
        The command to run the job
    logfile : `str`
        The path to the logfile

    Keywords
    --------
    run : `str`
        The run number
    batch : `str`
        Where to send the jobs
    batch_args : `str`
        Arguments to pass to batch command
    optstring : `str`
        Additional arguments to pass to the command
    dry_run : `bool`
        Print command but do not run it
    """
    run = kwargs.get('run', None)
    batch = kwargs.get('batch', 'native')
    batch_args = kwargs.get('batch_args', None)
    optstring = kwargs.get('optstring', None)
    dry_run = kwargs.get('dry_run', False)

    if batch.find('bsub') == 0:
        sub_com = "bsub -o %s" % logfile
        if batch_args is not None:
            sub_com += " %s " % batch_args
    elif batch.find('sbatch') == 0:
        batchfile = write_slurm_batchfile(jobname, logfile, **kwargs)
        sub_com = "sbatch %s" % batchfile
    elif batch.find('srun') == 0:
        sub_com = "srun --output %s" % logfile
        if batch_args is not None:
            sub_com += " %s " % batch_args
    else:
        sub_com = ""

    if batch.find('sbatch') < 0:
        if run is None:
            sub_com += " %s" % jobname
        else:
            sub_com += " %s --run %s" % (jobname, run)

        if optstring is not None:
            sub_com += " %s" % optstring

    if dry_run:
        sys.stdout.write("%s\n" % sub_com)
    else:
        os.system(sub_com)

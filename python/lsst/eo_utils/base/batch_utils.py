"""This module contains functions to help use the SLAC batch system"""

from __future__ import with_statement

import os
import sys

#import pipes

#from lsst.ctrl.pool import Batch, exportEnv, UMASK

def dispatch_job(jobname, logfile, **kwargs):
    """Dispatch a single job to the batch farm

    @param jobname (str)    The command to send to the batch
    @param run_num (str)    The run number, i.e,. '6106D'
    @param logfile (str)    The path to the logfile
    @param kwargs
            run (str)          The run number
            batch_args (str)   Arguments to pass to batch command
            optstring (str)    Additional arguments to pass to command
            dry_run (bool)     Print batch command but do not run it
            use_batch (bool)   Send command to batch farm
    """
    batch_args = kwargs.get('batch_args', None)
    optstring = kwargs.get('optstring', None)
    dry_run = kwargs.get('dry_run', False)
    run_num = kwargs.get('run', None)

    if kwargs.get('use_batch', False):
        sub_com = "bsub -o %s" % logfile
        if bsub_args is not None:
            sub_com += " %s " % batch_args
    else:
        sub_com = ""

    if run_num is None:
        sub_com += " %s" % jobname
    else:
        sub_com += " %s --run %s" % (jobname, run_num)

    if optstring is not None:
        sub_com += " %s" % optstring

    if dry_run:
        sys.stdout.write("%s\n" % sub_com)
    else:
        os.system(sub_com)

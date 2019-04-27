"""This module contains functions dispatch analysis jobs.

Eventually it should be able to handle jobs by:

1) Running them on the same cpu as the parent job
2) Running them on a multiprocees pool
3) Running them on a batch farm

"""

from __future__ import with_statement

import os
import sys

#import pipes

#from lsst.ctrl.pool import Batch, exportEnv, UMASK

def dispatch_job(jobname, logfile, **kwargs):
    """Dispatch a single job

    @param jobname (str)    The command to run the job
    @param logfile (str)    The path to the logfile
    @param kwargs
            run (str)          The run number
            batch (str)        Where to send the jobs
            batch_args (str)   Arguments to pass to batch command
            optstring (str)    Additional arguments to pass to the command
            dry_run (bool)     Print command but do not run it
    """
    run = kwargs.get('run', None)
    batch = kwargs.get('batch', 'native')
    batch_args = kwargs.get('batch_args', None)
    optstring = kwargs.get('optstring', None)
    dry_run = kwargs.get('dry_run', False)

    if batch.find('bsub') >= 0:
        sub_com = "bsub -o %s" % logfile
        if batch_args is not None:
            sub_com += " %s " % batch_args
    else:
        sub_com = ""

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

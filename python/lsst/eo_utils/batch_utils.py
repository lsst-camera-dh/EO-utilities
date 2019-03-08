#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to help use the SLAC batch system"""

from __future__ import with_statement

import os
import sys
#import pipes

#from lsst.ctrl.pool import Batch, exportEnv, UMASK

def dispatch_job(jobname, run_num, logfile, **kwargs):
    """Dispatch a single job to the batch farm

    @param jobname (str)    The command to send to the batch
    @param run_num (str)    The run number, i.e,. '6106D'
    @param logfile (str)    The path to the logfile
    @param kwargs
            bsub_args (str)    Arguments to pass to bsub command
            optstring (str)    Additional arguments to pass to command
            dry_run (bool)     Print batch command but do not run it
    """
    bsub_args = kwargs.get('bsub_args', None)
    optstring = kwargs.get('optstring', None)
    dry_run = kwargs.get('dry_run', False)

    bsub_com = "bsub -o %s" % logfile
    if bsub_args is not None:
        bsub_com += " %s" % bsub_args

    bsub_com += " %s --run %s" % (jobname, run_num)

    if optstring is not None:
        bsub_com += " %s" % optstring

    if dry_run:
        sys.stdout.write("%s\n" % bsub_com)
    else:
        os.system(bsub_com)


def read_runlist(filepath):
    """Read a list of runs from a txt file

    @param filepath (str)    The input file with the list of runs.
                             Each line should contain raft and run number, e.g.,
                             RTM-004-Dev 6106D

    @returns (list)          A list of tuples with (raft, run_num)
    """
    fin = open(filepath)
    lin = fin.readline()

    outlist = []
    while lin:
        tokens = lin.split()
        if len(tokens) == 2:
            outlist.append(tokens)
        lin = fin.readline()
    return outlist




"""


class LSFBatch(Batch):
    #Batch submission with lsf

    def execution(self, command):
        #Return execution string for script to be submitted
        script = [exportEnv(),
                  "umask %03o" % UMASK,
                  "cd %s" % pipes.quote(os.getcwd())]
        if self.verbose:
            script += ["echo \"mpiexec is at: $(which mpiexec)\"",
                       "ulimit -a",
                       "echo 'umask: ' $(umask)",
                       "eups list -s",
                       "export",
                       "date"]
        script += ["mpiexec %s %s" % (self.mpiexec, command)]
        if self.verbose:
            script += ["date",
                       "echo Done."]
        return "\n".join(script)


    def preamble(self, walltime=None):
        #The stuff in the exectution script
        if walltime is None:
            walltime = self.walltime
        if walltime <= 0:
            raise RuntimeError("Non-positive walltime: %s (did you forget '--time'?)" % (walltime,))
        if (self.numNodes <= 0 or self.numProcsPerNode <= 0) and self.numCores <= 0:
            raise RuntimeError(
                "Number of nodes (--nodes=%d) and number of processors per node (--procs=%d) not set OR "
                "number of cores (--cores=%d) not set" % (self.numNodes, self.numProcsPerNode, self.numCores))
        if self.numCores > 0 and (self.numNodes > 0 or self.numProcsPerNode > 0):
            raise RuntimeError("Must set either --nodes,--procs or --cores: not both")

        outputDir = self.outputDir if self.outputDir is not None else os.getcwd()
        filename = os.path.join(outputDir, (self.jobName if self.jobName is not None else "slurm") + ".o%j")
        return "\n".join([("#BSUB --nodes=%d" % self.numNodes) if self.numNodes > 0 else "",
                          ("#BSUB --ntasks-per-node=%d" % self.numProcsPerNode) if
                          self.numProcsPerNode > 0 else "",
                          ("#BSUB --ntasks=%d" % self.numCores) if self.numCores > 0 else "",
                          "#BSUB -W=%s" % walltime,
                          "#BSUB --job-name=%s" % self.jobName if self.jobName is not None else "",
                          "#BSUB -o=%s" % filename])


    def submitCommand(self, scriptName):
        #The command to run the script
        return "bsub %s" % (scriptName)

"""

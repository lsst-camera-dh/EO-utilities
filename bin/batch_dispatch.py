#!/usr/bin/env python

import os
import argparse

from batch_utils import read_runlist, dispatch_job

def main():
    """Hook for setup.py"""
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", default=None,
                        help="Text file with raft and run numbers")
    parser.add_argument("-j", "--jobname", default=None,
                        help="Name of job to execute")
    parser.add_argument("--logdir", default='logs',
                        help="Name of job to execute")
    parser.add_argument("--logsuffix", default='',
                        help="Suffisx to appned to log files ")
    parser.add_argument("--bsub_args", default="-W 600 -R bullet",
                        help="Arguents to pass to bsub command")
    parser.add_argument("--optstring", default=None,
                        help="Arguments to pass to job")
    parser.add_argument("--dry_run", default=False, action='store_true',
                        help="Print command, do not run job")

    args = parser.parse_args()

    run_list = read_runlist(args.input)

    opt_dict = dict(bsub_args=args.bsub_args,
                    optstring=args.optstring,
                    dry_run=args.dry_run)

    for run in run_list:

        raft = run[0]
        run_num = run[1]

        logfile = os.path.join(args.logdir, "%s_%s_%s%s.log" %\
                                   (raft, run_num, args.jobname.replace('.py', ''), args.logsuffix))
        dispatch_job(args.jobname, raft, run_num, logfile, **opt_dict)


if __name__ == '__main__':
    main()

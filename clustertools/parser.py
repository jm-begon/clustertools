# -*- coding: utf-8 -*-

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"



import argparse
from functools import partial
from clusterlib.scheduler import submit

def parse_args(description="Cluster job launcher.", args=None, namespace=None):
    """
    Parse the command line arguments with :mod:`argparse`

    Parameters
    ----------
    description: str, optional (default: "Cluster job launcher.")
        The program description


    Return
    ------
    submit: callable
        A submit function (cf. )
    """

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--backend", "-b", default="auto",
                        help="""{'auto', 'slurm', 'sge'}
        Backend where the job will be submitted. If 'auto', try detect
        the backend to use based on the commands available in the PATH
        variable looking first for 'slurm' and then for 'sge' if slurm is
        not found. The default backend selected when backend='auto' can also
        be fixed by setting the "CLUSTERLIB_BACKEND" environment variable.""")
    parser.add_argument("--logfolder", "-l", default=None,
                        help="""Specify the log directory. If None, no log
        directory is specified. Job logs will be at log_directory with the name
        ``job_name.job_id.txt`` where the ``job_id`` is given by the
        scheduler.""")
    parser.add_argument("--time", "-t", default="24:00:00",
                        help='Maximum time format "HH:MM:SS"')
    parser.add_argument("--memory", "-m", default=4000, type=int,
                        help="Maximum virtual memory in mega-bytes")
    parser.add_argument("--email", "-e", default=None,
                        help='Email where job information is sent. '
                             'If None, no email is asked to be sent')
    parser.add_argument("--emailopt", default=None,
                        help="""Specify email options:
            - SGE : Format char from beas (begin,end,abort,stop) for SGE.
            - SLURM : either BEGIN, END, FAIL, REQUEUE or ALL.
        See the documenation for more information""")
    parser.add_argument("--shell", "-s", default="#!/bin/bash",
                        help='Maximum time format "HH:MM:SS"')

    args = parser.parse_args(args=args, namespace=namespace)
    return partial(submit, time=args.time, memory=args.memory, email=args.email,
                   email_options=args.emailopt, log_directory=args.logfolder,
                   backend=args.backend, shell_script=args.shell)


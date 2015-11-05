# -*- coding: utf-8 -*-

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"



import argparse
from functools import partial

from clusterlib.scheduler import submit

from .util import get_log_folder


def parse_args(description="Cluster job launcher.", args=None, namespace=None):
    """
    Parse the command line arguments with :mod:`argparse`

    Parameters
    ----------
    description: str, optional (default: "Cluster job launcher.")
        The program description


    Return
    ------
    exp_name: str
        The experiment name
    script: str
        The path to the script
    script_builder: callable
        A submit function (cf. )
    """

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("name", help="The name of this experiment")
    parser.add_argument("script", help="Path to script")
    parser.add_argument("--backend", "-b", default="auto",
                        help="""{'auto', 'slurm', 'sge'}
        Backend where the job will be submitted. If 'auto', try detect
        the backend to use based on the commands available in the PATH
        variable looking first for 'slurm' and then for 'sge' if slurm is
        not found. The default backend selected when backend='auto' can also
        be fixed by setting the "CLUSTERLIB_BACKEND" environment variable.""")
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
    exp_name = args.name
    script = args.script
    script_builder = partial(submit, time=args.time, memory=args.memory,
                             email=args.email, email_options=args.emailopt,
                             log_directory=get_log_folder(exp_name),
                             backend=args.backend, shell_script=args.shell)
    return exp_name, script, script_builder

def parse_params(exp_name, description="Cluster job launcher.", args=None, namespace=None):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("database", help="The database on which to run")
    parser.add_argument("custopt", nargs="*",
                        help="Custom options to be passed on")
    parser.add_argument("--backend", "-b", default="auto",
                        help="""{'auto', 'slurm', 'sge'}
        Backend where the job will be submitted. If 'auto', try detect
        the backend to use based on the commands available in the PATH
        variable looking first for 'slurm' and then for 'sge' if slurm is
        not found. The default backend selected when backend='auto' can also
        be fixed by setting the "CLUSTERLIB_BACKEND" environment variable.""")
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
                        help='Maximum time in "HH:MM:SS" format')

    args = parser.parse_args(args=args, namespace=namespace)
    db = args.database
    custopt = args.custopt
    exp_name += db
    script_builder = partial(submit, time=args.time, memory=args.memory,
                             email=args.email, email_options=args.emailopt,
                             log_directory=get_log_folder(exp_name),
                             backend=args.backend, shell_script=args.shell)
    return script_builder, db, exp_name, custopt


# -*- coding: utf-8 -*-

import argparse
import sys
from functools import partial

<<<<<<< HEAD
from clusterlib.scheduler import submit

from .database import get_storage


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
    parser.add_argument("--shell", default="#!/bin/bash",
                        help='The shell to use')
    parser.add_argument("--capacity", "-c", default=sys.maxsize, type=int,
                        help="""The maximum number of job to launch
                        (default: sys.maxsize)""")
    parser.add_argument("--start", "-s", default=0, type=int,
                        help="""The index from which to start the computations
                        (default: 0)""")

    args = parser.parse_args(args=args, namespace=namespace)
    exp_name = args.name
    script = args.script
    log_folder = get_storage(exp_name).get_log_folder()
    script_builder = partial(submit, time=args.time, memory=args.memory,
                             email=args.email, email_options=args.emailopt,
                             log_directory=log_folder, backend=args.backend,
                             shell_script=args.shell)
    return exp_name, script, script_builder, {"capacity":args.capacity, "start":args.start}

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
    parser.add_argument("--shell", default="#!/bin/bash",
                        help='The shell in which to launch the jobs')
    parser.add_argument("--capacity", "-c", default=sys.maxsize, type=int,
                        help="""The maximum number of job to launch
                        (default: sys.maxsize)""")
    parser.add_argument("--start", "-s", default=0, type=int,
                        help="""The index from which to start the computations
                        (default: 0)""")
    parser.add_argument("--partition", "-p", default=None,
                        help="The cluster's partition/queue on which the computation will run.")
    parser.add_argument("--ntasks", "-j", default=None,
                        help="Number of processor to use for running each task (default to 1).")

    args = parser.parse_args(args=args, namespace=namespace)
    db = args.database
    custopt = args.custopt
    exp_name += db
    log_folder = get_storage(exp_name).get_log_folder()
    builder_partial = partial(submit, time=args.time, memory=args.memory,
                              email=args.email, email_options=args.emailopt,
                              log_directory=log_folder,
                              backend=args.backend, shell_script=args.shell)

    # optionally add additional flags
    additional_flags = dict()
    if args.partition is not None:
        additional_flags["partition"] = args.partition
    if args.ntasks is not None:
        additional_flags["ntasks"] = args.ntasks

    def script_builder(*nargs, **kwargs):
        return " ".join([
            builder_partial(*nargs, **kwargs),
            " ".join(["--{}={}".format(k, v) for k, v in additional_flags.items()])
        ])

    # build other params dict
    others = {"capacity": args.capacity, "start": args.start}
    others.update(additional_flags)

    return script_builder, db, exp_name, custopt, others
=======
from .environment import SlurmEnvironment, BashEnvironment, Serializer

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"
>>>>>>> v0.0.3


def positive_int(string):
    try:
        rtn = int(string)
        if rtn < 0:
            raise TypeError()
    except:
        raise TypeError("Expecting positive integer, got '{}' instead."
                        "".format(string))
    return rtn


def time_string(string):
    """Expecting "HH:MM:SS" format"""
    try:
        segments = string.split(":")
        if len(segments) == 3:
            hours, minutes, seconds = segments
        else:
            # MM:SS format
            hours = 0
            minutes, seconds = segments
        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)
        if hours < 0:
            raise TypeError()
        if not (0 <= minutes < 60):
            raise TypeError
        if not (0 <= seconds < 60):
            raise TypeError
    except:
        raise TypeError("Expecting '[HH:]MM:SS' format, got {} instead."
                        "".format(string))
    return string


def or_none(function):
    def convert(string):
        if string is None:
            return None
        return function(string)
    return convert


class BaseParser(object):
    def __init__(self, serializer_factory=Serializer,
                 description="Clustertool launcher"):
        self.serializer_factory = serializer_factory
        self.description = description

    def get_parser(self):
        parser = argparse.ArgumentParser(description=self.description)
        parser.add_argument("custom_option", nargs="*",
                            help="Options to be passed on")
        parser.add_argument("--capacity", "-c", default=sys.maxsize,
                            type=positive_int,
                            help="""The maximum number of job to launch
                                        (default: as much as possible)""")
        parser.add_argument("--start", "-s", default=0, type=positive_int,
                            help="""The index from which to start the computations
                                        (default: 0)""")
        parser.add_argument("--no_fail_fast", action="store_false",
                            default=True, help="If set, do not stop at the"
                                               "first error.")
        return parser

    def parse(self, args=None, namespace=None):
        parser = self.get_parser()
        args = parser.parse_args(args=args, namespace=namespace)
        environment = BashEnvironment(self.serializer_factory(),
                                      args.no_fail_fast)
        environment.run = partial(environment.run, start=args.start,
                                  capacity=args.capacity)

        return environment, args.custom_option


class ClusterParser(BaseParser):

    def get_parser(self):
        parser = super(ClusterParser, self).get_parser()
        parser.add_argument("--time", "-t", default="24:00:00",
                            type=time_string,
                            help='Maximum time; format "HH:MM:SS" '
                                 '(defaul: 24:00:00)')
        parser.add_argument("--memory", "-m", default=4000, type=positive_int,
                            help="Maximum virtual memory in mega-bytes "
                                 "(defaul: 4000)")
        parser.add_argument("--shell", default="#!/bin/bash",
                            help='The shell in which to launch the jobs')
        parser.add_argument("--partition", "-p", default=None,
                            type=or_none(str),
                            help='The partition on which to launch the job. '
                                 '(default: None; for the default partition')
        parser.add_argument("--n_proc", "-n", default=None, type=or_none(int),
                            help='The number of computation unit. '
                                 '(default: None; for only one')

        return parser

    def parse(self, args=None, namespace=None):
        parser = self.get_parser()
        args = parser.parse_args(args=args, namespace=namespace)
        environment = SlurmEnvironment(self.serializer_factory(),
                                       args.time,
                                       args.memory,
                                       args.partition,
                                       args.n_proc,
                                       args.shell,
                                       args.no_fail_fast)
        environment.run = partial(environment.run, start=args.start,
                                  capacity=args.capacity)
        return environment, args.custom_option

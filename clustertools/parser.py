# -*- coding: utf-8 -*-

import argparse
import sys
from functools import partial

from .environment import ClusterlibEnvironment, BashEnvironment, Serializer

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


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
        parser.add_argument("--backend", "-b", default="auto",
                            help="""{'auto', 'slurm', 'sge'}
                Backend where the job will be submitted. If 'auto', try detect
                the backend to use based on the commands available in the PATH
                variable looking first for 'slurm' and then for 'sge' if slurm
                is not found. """)
        parser.add_argument("--time", "-t", default="24:00:00",
                            type=time_string,
                            help='Maximum time; format "HH:MM:SS"')
        parser.add_argument("--memory", "-m", default=4000, type=positive_int,
                            help="Maximum virtual memory in mega-bytes")
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
        environment = ClusterlibEnvironment(self.serializer_factory(),
                                            args.time,
                                            args.memory,
                                            args.partition,
                                            args.n_proc,
                                            args.shell,
                                            args.no_fail_fast)
        environment.run = partial(environment.run, start=args.start,
                                  capacity=args.capacity)
        return environment, args.custom_option

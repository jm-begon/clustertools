# -*- coding: utf-8 -*-

import argparse
import sys
from functools import partial

from .environment import SlurmEnvironment, BashEnvironment, Serializer, \
    InSituEnvironment

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
    """
    `BaseParser`
    ============
    A parser is responsible for managing command line arguments and returning
    the adequate environment.

    Constructor parameters
    ----------------------
    serializer_factory: callable () --> Serializer instance
        A factory method to create the serializer

    description: str
        Description of the parser

    Note
    ----
    You can use the :meth:`add_argument` method which works the same way as its
    argparse homonym to add specific arguments
    """
    def __init__(self, serializer_factory=Serializer,
                 description="Clustertool launcher"):
        self.serializer_factory = serializer_factory
        parser = argparse.ArgumentParser(description=description)
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
        self.parser = parser

    def add_argument(self, *args, **kwargs):
        self.parser.add_argument(*args, **kwargs)

    def parse(self, args=None, namespace=None):
        args = self.parser.parse_args(args=args, namespace=namespace)
        environment = BashEnvironment(self.serializer_factory(),
                                      args.no_fail_fast)
        environment.run = partial(environment.run, start=args.start,
                                  capacity=args.capacity)

        return environment, args


class ClusterParser(BaseParser):

    def __init__(self, serializer_factory=Serializer,
                 description="Clustertool launcher"):
        super().__init__(serializer_factory, description)
        self.add_argument("--time", "-t", default="24:00:00",
                          type=time_string,
                          help='Maximum time; format "HH:MM:SS" '
                               '(defaul: 24:00:00)')
        self.add_argument("--memory", "-m", default=4000, type=positive_int,
                          help="Maximum virtual memory in mega-bytes "
                               "(defaul: 4000)")
        self.add_argument("--shell", default="#!/bin/bash",
                          help='The shell in which to launch the jobs')
        self.add_argument("--partition", "-p", default=None,
                          type=or_none(str),
                          help='The partition on which to launch the job. '
                               '(default: None; for the default partition')
        self.add_argument("--n_proc", "-n", default=None, type=or_none(int),
                          help='The number of computation unit. '
                               '(default: None; for only one')
        self.add_argument("--front-end", default=False, action="store_true",
                          help="Whether to run the code on the front end. "
                               "This is only provided for debugging purposes "
                               "(default: False)")
        self.add_argument("--gpu", default=None, type=or_none(int),
                          help="Request GPUs. Do not specify it for no GPU "
                               "(default: None)")

    def parse_unknown_args(self, unknown):
        args, kwargs = [], {}
        for arg in unknown:
            s = arg.split("=")
            if len(s) == 1:
                args.extend(s)
            elif len(s) == 2:
                kwargs[s[0]] = s[1]
            else:
                raise ValueError("Cannot parse {}: there cannot be more than "
                                 "one '='.".format(s))
        return args, kwargs

    def parse(self, args=None, namespace=None):
        args, other = self.parser.parse_known_args(args=args,
                                                   namespace=namespace)
        flags, options = self.parse_unknown_args(other)

        if args.front_end:
            environment = InSituEnvironment(fail_fast=args.no_fail_fast)
        else:
            environment = SlurmEnvironment(serializer=self.serializer_factory(),
                                           time=args.time,
                                           memory=args.memory,
                                           partition=args.partition,
                                           n_proc=args.n_proc,
                                           gpu=args.gpu,
                                           shell_script=args.shell,
                                           fail_fast=args.no_fail_fast,
                                           other_flags=flags,
                                           other_options=options)
        environment.run = partial(environment.run, start=args.start,
                                  capacity=args.capacity)
        return environment, args

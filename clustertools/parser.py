# -*- coding: utf-8 -*-

import argparse
import sys
import warnings
from abc import ABCMeta, abstractmethod
from functools import partial

from .environment import SlurmEnvironment, BashEnvironment, Serializer, \
    InSituEnvironment, FileSerializer, DebugEnvironment

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


class UniversalParser(argparse.ArgumentParser):
    def __init__(self,
                 prog=None,
                 usage=None,
                 description=None,
                 epilog=None,
                 parents=[],
                 formatter_class=argparse.HelpFormatter,
                 prefix_chars='-',
                 fromfile_prefix_chars=None,
                 argument_default=None,
                 conflict_handler='error',
                 add_help=True):
        super().__init__(prog=prog,
                         usage=usage,
                         description=description,
                         epilog=epilog,
                         parents=parents,
                         formatter_class=formatter_class,
                         prefix_chars=prefix_chars,
                         fromfile_prefix_chars=fromfile_prefix_chars,
                         argument_default=argument_default,
                         conflict_handler=conflict_handler,
                         add_help=add_help)

        self.add_argument("--capacity", "-c", default=sys.maxsize,
                          type=positive_int,
                          help="The maximum number of job to launch "
                               "(default: as much as possible)")
        self.add_argument("--start", "-s", default=0, type=positive_int,
                          help="The index from which to start the "
                               "computations (default: 0)")
        self.add_argument("--no_fail_fast", action="store_false",
                          default=True, help="If set, do not stop at the"
                                             "first error.")


class AbstractParser(object, metaclass=ABCMeta):
    """
    `BaseParser`
    ============
    A parser is responsible for managing command line arguments and returning
    the adequate environment.

    Constructor parameters
    ----------------------
    parser: an instance of argparse.Parser or None (default: None)

    Note
    ----
    You can use the :meth:`add_argument` method which works the same way as its
    argparse homonym to add specific arguments
    """
    def __init__(self, parser=None):
        if parser is None:
            parser = UniversalParser()
        self._parser = parser

    @property
    def parser(self):
        return self._parser

    def parse(self, args=None, namespace=None):
        namespace, other = self.parser.parse_known_args(args=args,
                                                        namespace=namespace)
        return self.create_environment(namespace, other), namespace

    @abstractmethod
    def create_environment_(self, namespace, other_args):
        pass

    def create_environment(self, namespace, other_args):
        environment = self.create_environment_(namespace, other_args)
        environment.run = partial(environment.run, start=namespace.start,
                                  capacity=namespace.capacity)
        return environment

    def add_argument(self, *args, **kwargs):
        # Shortcut
        self.parser.add_argument(*args, **kwargs)


class BashParser(AbstractParser):
    def __init__(self, parser=None, serializer_factory=Serializer):
        super().__init__(parser)
        self.serializer_factory = serializer_factory

    def create_environment_(self, namespace, other_args):
        environment = BashEnvironment(self.serializer_factory(),
                                      namespace.no_fail_fast)

        return environment


class BaseParser(BashParser):
    def __init__(self, serializer_factory=Serializer,
                 description="Clustertool launcher"):
        parser = UniversalParser(description=description)
        super().__init__(parser, serializer_factory)


class SlurmParser(AbstractParser):
    def __init__(self, parser=None, serializer_factory=Serializer):
        super().__init__(parser)
        self.serializer_factory = serializer_factory

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

    def create_environment_(self, namespace, other_args):
        flags, options = self.parse_unknown_args(other_args)

        return SlurmEnvironment(serializer=self.serializer_factory(),
                                time=namespace.time,
                                memory=namespace.memory,
                                partition=namespace.partition,
                                n_proc=namespace.n_proc,
                                gpu=namespace.gpu,
                                shell_script=namespace.shell,
                                fail_fast=namespace.no_fail_fast,
                                other_flags=flags,
                                other_options=options)


class ClusterParser(SlurmParser):
    def __init__(self, serializer_factory=Serializer,
                 description="Clustertool launcher"):
        parser = UniversalParser(description=description)
        super().__init__(parser, serializer_factory)


class DebugParser(AbstractParser):
    def __init__(self, parser=None):
        super().__init__(parser)
        self.add_argument("--verbose", action="store_true", default=False,
                          help="Whether to print more information "
                               "(default: False)")

    def create_environment_(self, namespace, other_args):
        return DebugEnvironment(print_all_parameters=namespace.verbose,
                                fail_fast=namespace.no_fail_fast)


class InSituParser(AbstractParser):
    def __init__(self, parser=None):
        super().__init__(parser)
        self.add_argument("--stdout", action="store_true", default=False,
                          help="Whether to print the log of the experiment "
                               "(not of clustertools) directly in the standard "
                               "output (default: False)")

    def create_environment_(self, namespace, other_args):
        return InSituEnvironment(stdout=namespace.stdout,
                                 fail_fast=namespace.no_fail_fast)


class CTParser(AbstractParser):
    def __init__(self, serializer_factory=FileSerializer,
                 description="Clustertool launcher"):
        parser = UniversalParser(description=description)
        super().__init__(parser)

        subparser = parser.add_subparsers(title="Backend",
                                          description="Choice of backend")

        # Debug
        debug_parser = subparser.add_parser("debug")
        debug_ct_parser = DebugParser(debug_parser)
        debug_parser.set_defaults(
            create_environment=debug_ct_parser.create_environment
        )

        # InSitu
        insitu_parser = subparser.add_parser("front-end")
        insitu_ct_parser = InSituParser(insitu_parser)
        insitu_parser.set_defaults(
            create_environment=insitu_ct_parser.create_environment
        )

        # Bash
        bash_parser = subparser.add_parser("bash")
        bash_ct_parser = BashParser(bash_parser, serializer_factory)
        bash_parser.set_defaults(
            create_environment=bash_ct_parser.create_environment
        )

        # Slurm
        slurm_parser = subparser.add_parser("slurm")
        slurm_ct_parser = SlurmParser(slurm_parser, serializer_factory)
        slurm_parser.set_defaults(
            create_environment=slurm_ct_parser.create_environment
        )

    def create_environment_(self, namespace, other_args):
        print(namespace)
        print(other_args)
        if not hasattr(namespace, "create_environment"):
            self.parser.print_help()
        else:
            return namespace.create_environment(namespace=namespace,
                                                other_args=other_args)

    def create_environment(self, namespace, other_args):
        # Changing the start/capacity will be done by the EnvParser
        return self.create_environment_(namespace, other_args)

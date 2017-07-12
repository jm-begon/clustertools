# -*- coding: utf-8 -*-

import sys
import subprocess
import logging
from time import time as epoch
from abc import ABCMeta, abstractmethod

from clusterlib.scheduler import submit

from .state import PendingState, AbortedState


__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


__RUN_SCRIPT__ = "ct_run"


class Session(object):
    """
    `Session`
    =========
    A `Session` is responsible for managing stateful information about a
    group of computations being run in a given environment
    """
    def __init__(self, parent_environment):
        self.environment = parent_environment
        self.exp_len = None
        self.storage = None
        self.n_launch = 0
        self.opened = False
        self.fail_fast = parent_environment.fail_fast
        self.logger = logging.getLogger("clustertools")

    def init(self, exp_len, storage):
        self.exp_len = exp_len
        self.storage = storage
        return self

    def is_open(self):
        return self.opened and self.exp_len is not None and \
               self.storage is not None

    def __enter__(self):
        self.n_launch = 0
        self.logger.info("Launching experiment '{exp_name}' in environment "
                         "'{cls}'"
                         "".format(exp_name=self.storage.exp_name,
                                   cls=repr(self.environment)))
        self.opened = True

    def run(self, lazy_computation):
        if not self.is_open():
            raise ValueError("The session has not been opened.")
        try:
            self.environment.issue(lazy_computation)
            self.storage.update_state(PendingState(lazy_computation.exp_name,
                                                   lazy_computation.comp_name))
            self.n_launch += 1
            self.logger.debug("Launching '{}'".format(repr(lazy_computation)))
        except Exception as exception:
            self.storage.update_state(AbortedState(lazy_computation.exp_name,
                                                   lazy_computation.comp_name,
                                                   exception))
            self.logger.warning("Could not launch '{}'. Reason: {}"
                                "".format(repr(lazy_computation),
                                          repr(exception)))
            if self.fail_fast:
                raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.info("Experiment '{exp_name}': {n_launch}/{exp_len} "
                         "computation(s)".format(exp_name=self.storage.exp_name,
                                                 n_launch=str(self.n_launch),
                                                 exp_len=str(self.exp_len)))
        self.closed = False


class Environment(object):
    """
    `Environment`
    =============
    The `Environment` controls how the computations of a given experiment
    must be run. It is a stateless component
    """
    __metaclass__ = ABCMeta

    def __init__(self, fail_fast=True):
        self.fail_fast = fail_fast

    def __repr__(self):
        return "{cls}(fail_fast={fail_fast})" \
               "".format(cls=self.__class__.__name__,
                         fail_fast=str(self.fail_fast))

    def run(self, experiment, start=0, capacity=None):

        with self.create_session(experiment) as session:
            for lazy_comp in experiment.yield_computations(repr(self),
                                                           start,
                                                           capacity):
                # a lazy_comp (lazy_computation) is a callable which runs
                # the computation
                session.run(lazy_comp)

    @abstractmethod
    def issue(self, lazy_computation):
        pass

    def create_session(self, experiment):
        return Session(self).init(len(experiment), experiment.storage)


class InSituEnvironment(Environment):
    def issue(self, lazy_computation):
        lazy_computation()


class BashEnvironment(Environment):
    def __init__(self, fail_fast=True, script=__RUN_SCRIPT__):
        super(BashEnvironment, self).__init__(fail_fast)
        self.script = script

    def __repr__(self):
        return "{cls}(fail_fast={fail_fast}, script={script})" \
               "".format(cls=self.__class__.__name__,
                         fail_fast=str(self.fail_fast),
                         script=self.script)

    def issue(self, lazy_computation):
        fpath = lazy_computation.serialize()
        job_command = "{python} {script_path} {serial_path}" \
                      "".format(python=sys.executable,
                                script_path=self.script,
                                serial_path=fpath).split(" ")
        log_file = lazy_computation.storage.get_log_prefix(epoch())

        subprocess.check_call(job_command, stdout=log_file, stderr=log_file)


class ClusterlibEnvironment(Environment):

    def __init__(self, time="1:00:00", memory=4000, partition=None,
                 n_proc=None, shell_script="#!/bin/bash", fail_fast=True,
                 script=__RUN_SCRIPT__, other_args=None):
        super(ClusterlibEnvironment, self).__init__(fail_fast)
        self.script = script
        self.time = time
        self.memory = memory
        self.shell_script = shell_script
        self.partition = partition
        self.n_proc = n_proc
        if other_args is None:
            other_args = {}
        self.other_args = other_args

    def __repr__(self):
        return "{cls}(time={time}, memory={memory}, partition={partition}, " \
               "n_proc={n_proc}, shell_script={shell}, fail_fast={fail_fast}, " \
               "script={script}, other_args={other})" \
               "".format(cls=self.__class__.__name__,
                         time=self.time,
                         memory=self.memory,
                         partition=self.partition,
                         n_proc=str(self.n_proc),
                         fail_fast=str(self.fail_fast),
                         script=self.script,
                         other=self.other_args)

    def issue(self, lazy_computation):
        fpath = lazy_computation.serialize()
        log_folder = lazy_computation.storage.get_log_folder()
        raw_cmd = "{python} {script_path} {serial_path}" \
                  "".format(python=sys.executable,
                            script_path=self.script,
                            serial_path=fpath).split(" ")
        command = submit(job_command=raw_cmd,
                         job_name=lazy_computation.comp_name,
                         time=self.time,
                         memory=self.memory,
                         log_directory=log_folder,
                         shell_script=self.shell_script)
        additional_flags = {k: v for k, v in self.other_args.items()}
        if self.partition is not None:
            additional_flags["partition"] = self.partition
        if self.n_proc is not None:
            additional_flags["ntasks"] = self.n_proc

        final_command = " ".join([command, " ".join(["--{}={}".format(k, v)
                                  for k, v in additional_flags.items()])])
        subprocess.check_output(final_command)


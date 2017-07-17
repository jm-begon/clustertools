# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import logging
from time import time as epoch
from abc import ABCMeta, abstractmethod
try:
    import cPickle as pickle
except ImportError:
    import pickle

from clusterlib.scheduler import submit

from .state import PendingState, AbortedState


__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


class Serializer(object):

    def __repr__(self):
        return "{cls}()".format(cls=self.__class__.__name__)

    def serialize(self, lazy_computation):
        """Return a unserializable string"""
        return pickle.dumps(lazy_computation, -1)

    def deserialize(self, serlialized):
        """Return the object represented by the serialized string"""
        return pickle.loads(serlialized)

    def serialize_and_script(self, lazy_computation):
        """Return a script to run the lazy_computation"""
        serialized = self.serialize(lazy_computation)
        return [sys.executable, '-c', 'from {mod} import {cls};'
                '{repr}({serialized})'
                ''.format(mod=__name__,
                          cls=self.__class__.__name__,
                          repr=repr(self),
                          serialized=repr(serialized))]

    def deserialize_and_run(self, serialized):
        lazy_computation = self.deserialize(serialized)
        lazy_computation()

    def __call__(self, serialized):
        self.deserialize_and_run(serialized)


class FileSerializer(Serializer):

    def serialize(self, lazy_computation):
        fname = "{}-{}.pkl".format(lazy_computation.comp_name, str(epoch()))
        fpath = lazy_computation.storage.get_messy_path(fname)
        with open(fpath, "wb") as hdl:
            pickle.dump(lazy_computation, hdl, -1)
        return fpath

    def deserialize(self, serlialized):
        with open(serlialized, "rb") as hdl:
            lazy_computation = pickle.load(hdl)
        try:
            os.remove(serlialized)
        except IOError:
            pass
        return lazy_computation


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
        return self

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
        self.opened = False


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
    # For debugging purpose

    def __init__(self, serializer=Serializer(), fail_fast=True):
        super(BashEnvironment, self).__init__(fail_fast)
        # Since Serializer is totally stateless, it can be shared among
        # several instances
        self.serializer = serializer

    def __repr__(self):
        return "{cls}(serializer={serializer}, fail_fast={fail_fast})" \
               "".format(cls=self.__class__.__name__,
                         fail_fast=repr(self.fail_fast),
                         serializer=repr(self.serializer))

    def issue(self, lazy_computation):
        job_command = self.serializer.serialize_and_script(lazy_computation)

        storage = lazy_computation.storage
        log_file = storage.get_log_prefix(lazy_computation.comp_name,
                                          "-{}".format(str(epoch())))

        with open(log_file, "w") as log_hdl:
            subprocess.check_call(job_command, stdout=log_hdl, stderr=log_hdl)


class ClusterlibEnvironment(Environment):

    def __init__(self, serializer=Serializer(), time="1:00:00", memory=4000,
                 partition=None, n_proc=None, shell_script="#!/bin/bash",
                 fail_fast=True, other_args=None):
        super(ClusterlibEnvironment, self).__init__(fail_fast)
        self.serializer = serializer
        self.time = time
        self.memory = memory
        self.shell_script = shell_script
        self.partition = partition
        self.n_proc = n_proc
        if other_args is None:
            other_args = {}
        self.other_args = other_args

    def __repr__(self):
        return "{cls}(serializer={serializer}, time={time}, memory={memory}, " \
               "partition={partition}, n_proc={n_proc}, shell_script={shell}, "\
               "fail_fast={fail_fast}, other_args={other})" \
               "".format(cls=self.__class__.__name__,
                         serializer=repr(self.serializer),
                         time=repr(self.time),
                         memory=repr(self.memory),
                         partition=repr(self.partition),
                         n_proc=repr(self.n_proc),
                         fail_fast=repr(self.fail_fast),
                         shell=self.shell_script,
                         other=repr(self.other_args))

    def issue(self, lazy_computation):
        log_folder = lazy_computation.storage.get_log_folder()
        ls_cmd = self.serializer.serialize_and_script(lazy_computation)
        raw_cmd = " ".join(ls_cmd)
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

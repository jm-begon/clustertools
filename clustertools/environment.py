# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import logging
from time import time as epoch
from abc import ABCMeta, abstractmethod
from shlex import quote as escape

import dill

from .state import PendingState, AbortedState

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


class Serializer(object):

    def __repr__(self):
        return "{cls}()".format(cls=self.__class__.__name__)

    def serialize(self, lazy_computation):
        """Return a unserializable string"""
        return dill.dumps(lazy_computation, -1)

    def deserialize(self, serlialized):
        """Return the object represented by the serialized string"""
        return dill.loads(serlialized)

    def serialize_and_script(self, lazy_computation):
        """Return a script to run the lazy_computation"""
        serialized = self.serialize(lazy_computation)
        return [sys.executable, '-c',
                'from {mod} import {cls};'
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
            dill.dump(lazy_computation, hdl, -1)
        return fpath

    def deserialize(self, serlialized):
        with open(serlialized, "rb") as hdl:
            lazy_computation = dill.load(hdl)
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
        """

        Parameters
        ----------
        lazy_computation

        Returns
        -------
        success: bool
            Whether launching the `lazy_computation` was (apparently) a
            success
        """
        if not self.is_open():
            raise ValueError("The session has not been opened.")
        try:
            self.storage.update_state(PendingState(lazy_computation.exp_name,
                                                   lazy_computation.comp_name))
            self.environment.issue(lazy_computation)
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
            return False

        return True

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

    The `Environment` runs a experiment. To do so, it creates a `Session`.
    The `Session` is the stateful component which is responsible for:
     - counting the number of expirement run
     - logging everything
     - enforcing the capacity constraint
    A `Session` should not be created directly.
    Finally, the `Session` issues the computation through the `Environment`.
    """
    __metaclass__ = ABCMeta

    def __init__(self, fail_fast=True):
        self.fail_fast = fail_fast

    def __repr__(self):
        return "{cls}(fail_fast={fail_fast})" \
               "".format(cls=self.__class__.__name__,
                         fail_fast=str(self.fail_fast))

    def run(self, experiment, start=0, capacity=None):
        """

        Parameters
        ----------
        experiment
        start
        capacity

        Returns
        -------
        error_count: int >= 0
            The number of computations that could not be launched
        """
        error_count = 0
        with self.create_session(experiment) as session:
            for lazy_comp in experiment.yield_computations(repr(self),
                                                           start,
                                                           capacity):
                # a lazy_comp (lazy_computation) is a callable which runs
                # the computation
                if not session.run(lazy_comp):
                    error_count += 1
        return error_count

    @abstractmethod
    def issue(self, lazy_computation):
        """
        Actually launch the `lazy_computation`

        Parameters
        ----------
        lazy_computation: lazyfied `Computation`
            The computation to launch

        Exception
        ---------
        Will throw an exception if an error occurred during the launching. If
        no exception is raised, the launching is (apparently) fine
        """
        pass

    def create_session(self, experiment):
        return Session(self).init(len(experiment), experiment.storage)


class InSituEnvironment(Environment):
    """
    InSituEnvironment
    =================
    An `Environment` that runs the code in a sequential way, in the current
    process.

    Constructor Parameters
    ----------------------
    stdout: boolean (defaul: False)
        Whether to print on the standard output rather than redirect
        to a log file. Setting False is the standard way for environment.
    fail_fast: boolean (default: True
    """
    def __init__(self, stdout=False, fail_fast=True):
        super().__init__(fail_fast)
        self.stdout = stdout

    def __repr__(self):
        return "{cls}(stdout={stdout}, fail_fast={fail_fast})"\
               "".format(cls=self.__class__.__name__,
                         stdout=repr(self.stdout),
                         fail_fast=self.fail_fast)

    def issue(self, lazy_computation):
        if self.stdout:
            lazy_computation()
            return

        storage = lazy_computation.storage
        log_file = storage.get_log_prefix(lazy_computation.comp_name,
                                          "-{}".format(str(epoch())))
        sys_backup = sys.stdout, sys.stderr
        try:
            with open(log_file, "w") as hdl:
                sys.stdout = sys.stderr = hdl
                lazy_computation()
        finally:
            sys.stdout, sys.stderr = sys_backup


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

        # Dirty hack: since we don't want to wait for the computation to end
        # for closing the file, we leave it as is.
        # For sequential computation `InSituEnvironment` is much cleaner
        file_handle = open(log_file, "w")
        subprocess.Popen(job_command, stderr=file_handle, stdout=file_handle)


class SlurmEnvironment(Environment):

    def __init__(self, serializer=Serializer(), time="1:00:00", memory=4000,
                 partition=None, n_proc=None, shell_script="#!/bin/bash",
                 fail_fast=True, other_args=None):
        super(SlurmEnvironment, self).__init__(fail_fast)
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
        # Making Slurm command
        comp_name = lazy_computation.comp_name
        log_folder = lazy_computation.storage.get_log_folder()
        log_prefix = os.path.join(log_folder, comp_name)

        slurm_cmd = ["sbatch", "--job-name={}".format(comp_name),
                     "--time={}".format(self.time),
                     "--mem={}".format(self.memory),
                     "--output={}.%j.txt".format(log_prefix),
                     ]

        if self.partition is not None:
            slurm_cmd.append("--partition={}".format(self.partition))

        if self.n_proc is not None:
            slurm_cmd.append("--ntasks={}".format(self.n_proc))

        for flag, value in self.other_args.items():
            slurm_cmd.append("--{}={}".format(flag, value))

        # Making computation command
        cmd_as_tuple = self.serializer.serialize_and_script(lazy_computation)
        str_cmd = " ".join([escape(s) for s in cmd_as_tuple])
        whole_cmd = "{shell}\n{cmd}".format(shell=self.shell_script,
                                            cmd=str_cmd)

        logger = logging.getLogger("clustertools")
        logger.debug(slurm_cmd)
        logger.debug(whole_cmd)

        # Running everything
        # Slurm commands are launched through shell.
        # 1. We can either dump a bash program and then create a subprocess
        #    to launch it
        # 2. Or we can pipe directly both part. This is the option we take
        #    here.
        with subprocess.Popen(slurm_cmd, stdin=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              stdout=subprocess.PIPE) as process:
            stdout, stderr = process.communicate(whole_cmd.encode("utf-8"))
            stdout = stdout.decode("utf-8")
            stderr = stderr.decode("utf-8")
            logger.debug(stdout)

            if len(stderr) > 0:
                logger.error(stderr)
            if process.returncode != 0:
                logger.error("Return code:", process.returncode)
                raise subprocess.CalledProcessError(process.returncode,
                                                    cmd=slurm_cmd,
                                                    stdout=stdout,
                                                    stderr=stderr)


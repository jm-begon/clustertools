# -*- coding: utf-8 -*-
import os
import random
from collections import defaultdict
from unittest import SkipTest

from nose import with_setup

from clustertools.environment import Environment
from clustertools.experiment import Computation
from clustertools.storage import Architecture, PickleStorage, Storage

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

__EXP_NAME__ = "ClustertoolsTest"


def get_exp_name():
    return "{}_{}".format(__EXP_NAME__, os.getpid())


class IntrospectStorage(Storage):
    """
    This `Storage` does not store anything on disk but rather keeps track
    of everything that has happened.

    Attributes
    ----------
    state_history: mapping: computation_name -> list of `State`
        The list of state of that computation (most recent at the end)
    result_history: mapping: computation_name -> list of saved results
        The list of results of that computation (most recent at the end)
    """
    def __init__(self, experiment_name, architecture=Architecture()):
        super(IntrospectStorage, self).__init__(experiment_name, architecture)
        self.state_history = defaultdict(list)
        self.result_history = defaultdict(list)
        self.parameter_set_history = defaultdict(list)

    def update_state(self, state):
        self.state_history[state.comp_name].append(state)
        return state

    def load_states(self):
        return [states[-1] for states in self.state_history.values()]

    def load_state(self, comp_name):
        s = self.state_history.get(comp_name, None)
        if s is None:
            return None
        return s[-1]

    def _save_r_dict(self, comp_name, r_dict):
        self.result_history[comp_name].append(r_dict)

    def _load_r_dict(self, comp_name):
        return self.result_history[comp_name][-1]

    def _load_r_dicts(self):
        return {comp_name: history[-1] for comp_name, history
                in self.result_history.items()}

    def save_parameter_set(self, parameter_set):
        self.parameter_set_history[self.exp_name].append(parameter_set)


def purge(exp_name=__EXP_NAME__, storage_factory=IntrospectStorage):
    storage = storage_factory(experiment_name=exp_name)
    try:
        storage.delete()
    except OSError:
        pass
    return storage


def pickle_purge(exp_name=None):
    exp_name = get_exp_name() if exp_name is None else exp_name
    purge(exp_name, PickleStorage)


def prep(exp_name=None, storage_factory=IntrospectStorage):
    exp_name = get_exp_name() if exp_name is None else exp_name
    storage = purge(exp_name, storage_factory)
    storage.init()


def pickle_prep(exp_name=None):
    exp_name = get_exp_name() if exp_name is None else exp_name
    prep(exp_name, PickleStorage)


def with_setup_(setup=None, teardown=None):
    """Decorator like `with_setup` of nosetest but which can be applied to any
    function"""
    def decorated(function):
        def app(*args, **kwargs):
            if setup:
                setup()
            try:
                function(*args, **kwargs)
            finally:
                if teardown:
                    teardown()
        return app
    return decorated


# Loosely based on clusterlib (https://github.com/clusterlib/clusterlib)
def skip_if_usuable(environment_cls):
    def skip_or_not():
        if not environment_cls.is_usable():
            raise SkipTest("Environment '{}' is not usable here"
                           "".format(repr(environment_cls)))

    return with_setup(skip_or_not)


class TestComputation(Computation):
    def __init__(self, exp_name=None, comp_name="TestComp",
                 context="n/a", storage_factory=IntrospectStorage):
        exp_name = get_exp_name() if exp_name is None else exp_name
        super(TestComputation, self).__init__(exp_name=exp_name,
                                              comp_name=comp_name,
                                              context=context,
                                              storage_factory=storage_factory)

    def run(self, collector, x1, x2, **ignored):
        collector["mult"] = x1 * x2


class InterruptedComputation(Computation):
    def __init__(self, exp_name=None, comp_name="TestComp",
                 context="n/a", storage_factory=IntrospectStorage):
        exp_name = get_exp_name() if exp_name is None else exp_name
        super().__init__(exp_name=exp_name,
                         comp_name=comp_name,
                         context=context,
                         storage_factory=storage_factory)

    def run(self, collector, **parameters):
        raise KeyboardInterrupt()


class ListUpJobs(Environment):

    user = "skywalker"
    jobs = ["save_galaxy"]

    @classmethod
    def is_usable(cls):
        return True

    @classmethod
    def list_up_jobs(cls, user=None):
        if user == cls.user:
            return [x for x in cls.jobs]
        return []





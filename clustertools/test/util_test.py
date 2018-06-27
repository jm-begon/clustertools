# -*- coding: utf-8 -*-

from collections import defaultdict
from unittest import SkipTest

from nose import with_setup

from clustertools.experiment import Result, Computation, PartialComputation
from clustertools.storage import Storage, Architecture, PickleStorage

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

__EXP_NAME__ = "ClustertoolsTest"


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

    def update_state(self, state):
        self.state_history[state.comp_name].append(state)
        return state

    def load_states(self):
        return [states[-1] for states in self.state_history.values()]

    def _save_r_dict(self, comp_name, r_dict):
        self.result_history[comp_name].append(r_dict)

    def _load_r_dict(self, comp_name):
        return self.result_history[comp_name][-1]

    def _load_r_dicts(self):
        return {comp_name: history[-1] for comp_name, history
                in self.result_history.items()}


def purge(exp_name=__EXP_NAME__, storage_factory=IntrospectStorage):
    storage = storage_factory(experiment_name=exp_name)
    try:
        storage.delete()
    except OSError:
        pass
    return storage


def pickle_purge(exp_name=__EXP_NAME__):
    purge(exp_name, PickleStorage)


def prep(exp_name=__EXP_NAME__, storage_factory=IntrospectStorage):
    storage = purge(exp_name, storage_factory)
    storage.init()


def pickle_prep(exp_name=__EXP_NAME__):
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
    def __init__(self, exp_name=__EXP_NAME__, comp_name="TestComp",
                 context="n/a", storage_factory=IntrospectStorage):
        super(TestComputation, self).__init__(exp_name=exp_name,
                                              comp_name=comp_name,
                                              context=context,
                                              storage_factory=storage_factory)

    def run(self, x1, x2, **ignored):
        result = Result("mult")
        result.mult = x1*x2
        return result


class TestPartialComputation(PartialComputation):
    def __init__(self, exp_name=__EXP_NAME__, comp_name="TestComp",
                 context="n/a", storage_factory=IntrospectStorage):
        super(TestPartialComputation, self).__init__(exp_name=exp_name,
                                                     comp_name=comp_name,
                                                     context=context,
                                                     storage_factory=storage_factory)

    def run(self, n, **ignored):
        result = Result("i")
        for i in range(n):
            if i >= 3:
                raise ValueError("Parameter n cannot be greater than 3.")
            result.i = i
            yield result
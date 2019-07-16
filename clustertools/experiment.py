# -*- coding: utf-8 -*-

"""
Module :mod:`experiment` is a set of functions and classes to build, run and
monitor experiments

Restriction
-----------
Experiment names should always elligible file names.
"""

import sys
from abc import ABCMeta, abstractmethod


import logging
from functools import partial

from clustertools.util import SigHandler
from .storage import PickleStorage, __PARAMETERS__, __RESULTS__
from .state import LaunchableState, RunningState, Monitor


__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


class Result(dict):
    """
    ``Result``
    ==========
    A result is a place holder for pairs metric=value
    """
    def __init__(self, *metric_names, **kwargs):
        kwargs.update({k: None for k in metric_names})
        super(Result, self).__init__(kwargs)

    def __setattr__(self, key, value):
        self[key] = value

    def __dir__(self):
        return self.keys()

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setstate__(self, state):
        # cf. https://github.com/scikit-learn/scikit-learn/issues/6196.
        pass

    def __repr__(self):
        kwargs = ", ".join(["{k}={v}".format(k=k, v=v) for k,v in self.items()])
        return "{cls}({kwargs})".format(cls=self.__class__.__name__,
                                        kwargs=kwargs)


class Computation(object):
    """
    `Computation`
    =============
    A ``Computation`` is any computation that must be run as part of an
    experiment on a given set of parameters

    Constructor parameters
    ----------------------
    exp_name: str
        The name of the experiment
    comp_name: str
        The name of the computation
    context: str (optional)
        Context information (can be the time/memory requirements, for instance)
    storage_factory: callable str -> cls:`Storage`
        A factory which takes as input the experiment name and returns
        a cls:`Storage` instance
    """
    __metaclass__ = ABCMeta

    @classmethod
    def partialize(cls, **kwargs):
        return partial(cls, **kwargs)

    def __init__(self, exp_name, comp_name, context="n/a",
                 storage_factory=PickleStorage):
        if storage_factory is None:
            storage_factory = PickleStorage
        if context is None:
            context = "n/a"
        self.exp_name = exp_name
        self.comp_name = comp_name
        self.context = context
        self.storage = storage_factory(experiment_name=self.exp_name)
        self.current_state = LaunchableState(self.comp_name)
        self.result = None
        self.parameters = {}

    def __repr__(self):
        return "{cls}(exp_name={exp_name}, comp_name={comp_name}, " \
               "context={context}, " \
               "storage_factory={storage_factory}).lazyfiy(**{parameters})" \
               "".format(cls=self.__class__.__name__,
                         exp_name=repr(self.exp_name),
                         comp_name=repr(self.comp_name),
                         context=repr(self.context),
                         storage_factory=self.storage.__class__.__name__,
                         parameters=repr(self.parameters))

    @abstractmethod
    def run(self, result, **parameters):
        pass

    def notify_progress(self, progress):
        self.current_state = self.storage.update_state(self.current_state.update_progress(progress))

    def save_result(self, result=None):
        if result is not None:
            self.result = result

        self.current_state = self.storage.update_state(self.current_state.to_critical())
        self.storage.save_result(self.comp_name, self.parameters, self.result,
                                 self.context)
        self.current_state = self.storage.update_state(self.current_state.to_partial())

    def _interrupt_handler(self, exception):
        self.storage.update_state(self.current_state.is_not_up())
        logging.getLogger("clustertools").warning("Job got interrupted: {}"
                                                  "".format(repr(exception)),
                                                  exc_info=exception)

    def __call__(self, **parameters):
        actual_parameters = {k: v for k, v in self.parameters.items()}
        actual_parameters.update(parameters)
        with SigHandler(self._interrupt_handler):
            self.current_state = self.storage.update_state(RunningState(self.comp_name))
            if self.result is None:
                self.result = Result(repr=repr(self))
            try:
                self.run(self.result, **actual_parameters)
                self.notify_progress(1.)
                self.save_result(self.result)
                self.current_state = self.storage.update_state(self.current_state.to_completed())
            except Exception as exception:
                self.storage.update_state(self.current_state.abort(exception))
                raise
        return self.result

    def lazyfy(self, **parameters):
        self.parameters = parameters
        return self


class Experiment(object):

    @classmethod
    def name_computation(cls, exp_name, index):
        return "Computation-{}-{:d}".format(exp_name, index)

    def __init__(self, exp_name, parameter_set, computation_factory,
                 storage_factory=PickleStorage, user=None):
        self.exp_name = exp_name
        self.parameter_set = parameter_set
        self.comp_factory = computation_factory
        self.storage_factory = storage_factory
        self.monitor = Monitor(exp_name, user, storage_factory)

    @property
    def storage(self):
        return self.monitor.storage

    def yield_computations(self, context="n/a", start=0, capacity=None,
                           auto_refresh=False):
        if capacity is None:
            capacity = sys.maxsize

        self.monitor.refresh()
        storage = self.monitor.storage
        storage.init()
        self.storage.save_parameter_set(self.parameter_set)
        unlaunchable = self.monitor.unlaunchable_comp_names()

        storage_factory = self.storage_factory

        i = 0
        for j, param_dict in self.parameter_set:
            if j < start:
                continue
            if i >= capacity:
                break
            if auto_refresh:
                self.monitor.refresh()
                unlaunchable = self.monitor.unlaunchable_comp_names()

            label = Experiment.name_computation(self.exp_name, j)
            if label in unlaunchable:
                continue

            computation = self.comp_factory(exp_name=self.exp_name,
                                            comp_name=label,
                                            context=context,
                                            storage_factory=storage_factory)

            yield computation.lazyfy(**param_dict)

            i += 1

    def __iter__(self):
        for x in self.yield_computations():
            yield x

    def __len__(self):
        return len(self.parameter_set)


def load_computation(exp_name, index):
    comp_name = Experiment.name_computation(exp_name, index)
    storage = PickleStorage(exp_name)
    r_dict = storage._load_r_dict(comp_name)[comp_name]
    return r_dict[__PARAMETERS__], r_dict[__RESULTS__]


def load_computation_by_params(exp_name, **parameters):
    """Load parameters and results from a computation based on its parameters.
    Parameters
    ----------
    exp_name: str
        Name of the experiment
    parameters: dict
        Dictionary mapping parameter name to its value.

    Returns
    -------
    index: int
        Computation index
    computation: tuple
        Tuple containing the parameters (0) and the results (1).
    """
    from .parameterset import build_parameter_set
    param_set = build_parameter_set(exp_name)
    indices = list(param_set.get_indices_with(**{k: {v} for k, v in parameters.items()}))
    if len(indices) > 1:
        raise ValueError("Too many computations with this combination of parameters (found: {}). Can only load one."
                         "".format(indices))
    elif len(indices) == 0:
        raise ValueError("No computation found with those parameters.")
    return indices[0], load_computation(exp_name, indices[0])

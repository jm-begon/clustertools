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

from clustertools.chrono import Watch, BrokenWatch
from clustertools.util import SigHandler
from .storage import PickleStorage, __PARAMETERS__, __RESULTS__
from .state import LaunchableState, RunningState, Monitor, IncompleteState

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
        # cf. https://github.com/scikit-learn/scikit-learn/issues/6196
        pass

    def __repr__(self):
        kwargs = ", ".join(["{k}={v}".format(k=k, v=v) for k,v in self.items()])
        return "{cls}({kwargs})".format(cls=self.__class__.__name__,
                                        kwargs=kwargs)


class Collector(object):
    """
    `Collector`
    ==================
    The `Collector` has two responsibilities:
     1. Manage de stateful part of the computation (update the state, etc.)
     2. Collect input from the user (progress, laps, result)
    """
    def __init__(self, comp_name, parameters, storage, context="n/a",
                 repr="n/a"):

        self.comp_name = comp_name
        self.parameters = parameters
        self.comp_storage = storage.specialize(comp_name)
        self.current_state = LaunchableState(comp_name)
        self.current_context = context
        self.watch = None
        self.result = None
        self.repr = repr
        self.contexts = []

    def get_interrupt_handler(self):
        def interrupt_handler(exception):
            self.current_state = self.comp_storage.update_state(self.current_state.is_not_up())
            logging.getLogger("clustertools").warning("Job got interrupted: {}"
                                                      "".format(repr(exception)),
                                                      exc_info=exception)
        return interrupt_handler

    def __setitem__(self, key, value):
        self.result[key] = value

    def __getitem__(self, item):
        return self.result[item]

    def __enter__(self):
        previous_state = self.comp_storage.load_state()
        if isinstance(previous_state, IncompleteState):
            # Reload everything for restart
            contexts, watch, result = self.comp_storage.load_context_watch_result()
            self.contexts = contexts
            self.result = result
            # Reset the watch and the progress monitor of the state
            self.watch = Watch.reset(watch)
            previous_state.reset_progress_monitor(watch.progress_monitor)
            self.current_state = previous_state

        else:
            # Start from scratch
            self.current_state = LaunchableState(self.comp_name)
            self.watch = Watch(self.current_state.progress_monitor)
            self.result = Result()

        self.contexts.append(self.current_context)
        self.watch.__enter__()
        self.current_state = self.comp_storage.update_state(RunningState.from_(self.current_state))

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.watch.__exit__(exc_type, exc_val, exc_tb)
        if isinstance(exc_val, KeyboardInterrupt):
            # Has been handled already
            return False
        elif exc_val is not None:
            self.current_state = self.comp_storage.update_state(self.current_state.abort(exc_val))
            return False  # re-raise the exception

        self.save_result()
        self.current_state = self.comp_storage.update_state(self.current_state.to_completed())

    def update_progress(self, progress):
        self.watch.update_progress(progress)
        self.current_state = self.comp_storage.update_state(self.current_state)

    def new_lap(self, label=None):
        self.watch.new_lap(label)

    def save_result(self, parameters=None):
        if parameters is None:
            parameters = self.parameters
        self.current_state = self.comp_storage.update_state(self.current_state.to_critical())
        self.comp_storage.save_result(parameters, self.result, self.contexts,
                                      self.watch, self.repr)
        self.current_state = self.comp_storage.update_state(self.current_state.to_partial())


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
                 storage_factory=None):
        if storage_factory is None:
            storage_factory = PickleStorage
        if context is None:
            context = "n/a"
        self.exp_name = exp_name
        self.comp_name = comp_name
        self.context = context
        self.storage = storage_factory(exp_name)
        self.parameters = {}

    def __repr__(self):
        args = [
            "exp_name={}".format(repr(self.exp_name)),
            "comp_name={}".format(repr(self.comp_name)),
            "context={}".format(repr(self.context)),
        ]
        if type(self.storage) != PickleStorage:
            args.append("storage_factory={}".format(type(self.storage)))

        return "{cls}({args}).lazyfy(**{parameters})" \
               "".format(cls=self.__class__.__name__,
                         args=", ".join(args),
                         parameters=repr(self.parameters))

    @abstractmethod
    def run(self, collector, **parameters):
        pass

    def __call__(self, **parameters):
        actual_parameters = {k: v for k, v in self.parameters.items()}
        actual_parameters.update(parameters)
        with Collector(self.comp_name, actual_parameters,
                       self.storage, self.context, repr(self)) as collector, \
            SigHandler(collector.get_interrupt_handler()):

            self.run(collector, **actual_parameters)
            result = collector.result
        return result

    def lazyfy(self, **parameters):
        self.parameters = parameters
        return self

    def has_parameters(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.parameters or \
               self.parameters[key] != value:
                return False
        return True


class ScriptComputation(Computation):
    @classmethod
    def format_args(cls, dict):
        return ["--{} {}".format(k, v) for k, v in dict.items()]

    def run(self, collector, script_path, **kwargs):
        import subprocess

        cmd = [script_path] + self.__class__.format_args(kwargs)

        proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)

        print(proc.stdout)
        collector["return_code"] = proc.returncode


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

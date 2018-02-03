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
from itertools import product as cartesian_product
from collections import defaultdict

from .storage import PickleStorage
from .state import RunningState, Monitor


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

    def __init__(self, exp_name, comp_name, context="n/a",
                 storage_factory=PickleStorage):
        self.exp_name = exp_name
        self.comp_name = comp_name
        self.context = context
        self.storage = storage_factory(experiment_name=self.exp_name)
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
    def run(self, **parameters):
        pass

    def __call__(self, **parameters):
        actual_parameters = {k: v for k, v in self.parameters.items()}
        actual_parameters.update(parameters)
        state = RunningState(self.exp_name, self.comp_name)
        self.storage.update_state(state)
        try:
            result = self.run(**actual_parameters)
            state = self.storage.update_state(state.to_critical())
            self.storage.save_result(self.comp_name, actual_parameters, result,
                                     self.context)

            state = self.storage.update_state(state.to_completed())
        except Exception as exception:
            self.storage.update_state(state.abort(exception))
            raise
        return result

    def lazyfy(self, **parameters):
        self.parameters = parameters
        return self


class PartialComputation(Computation):
    """
    Expect the run method to be a generator
    """
    __metaclass__ = ABCMeta

    def __call__(self, **parameters):
        actual_parameters = {k: v for k, v in self.parameters.items()}
        actual_parameters.update(parameters)
        state = RunningState(self.exp_name, self.comp_name)
        self.storage.update_state(state)
        partial_result = Result()
        try:
            for partial_result in self.run(**actual_parameters):
                state = self.storage.update_state(state.to_critical())
                self.storage.save_result(self.comp_name, actual_parameters,
                                         partial_result, self.context)
                state = self.storage.update_state(state.to_partial())
            state = self.storage.update_state(state.to_completed())
        except Exception as exception:
            self.storage.update_state(state.abort(exception))
            raise
        return partial_result


class ParameterSet(object):
    """
    `ParameterSet`
    ==============
    A `ParameterSet` is a structure yielding parameter tuples. A parameter tuple
    `pt` is an ordered list of values such that `pt[i]` is an admissible value
    for parameter `i`. For the sake of ambiguity, a parameter
    tuple can be referred to as a multidimensional parameter, which can be
    abbreviated to "parameter" (dropping the plural to raise the confusion
    with single-dimension parameters).

    A parameter is either a metadata, if it can only take one value, or a
    variable, if it can take several values. The set of values a parameter can
    take is referred as its domain.

    To entertain confusion further, "parameter" can refer to the name
    of the parameter, the value it takes, both or to the mapping between
    the name and the domain. Enjoy!

    Parameter tuples are generated as the cartesian product of the parameters
    domain, ordered following the lexicographic order of the parameter names
    and according the separator: all the tuples of the domains defined before
    the separator must be yielded before enlarging the domains with was comes
    after the separator.

    The separator allows for two use cases:
      1. Force an ordering on the computations (do more important stuff first)
      2. Make more computation after the first round


    Constructor parameters
    ----------------------
    param_map_seq: sequence of mapping str -> set, or None (default: None)
        Each mapping defines one or several bindings of the type "parameter name
        (i.e. the string)-domain (i.e. the set)". The sequence represents
        partial domains isolated by separators.
    """
    def __init__(self, param_map_seq=None):
        if param_map_seq:
            self.param_map_seq = list(param_map_seq)
        else:
            self.param_map_seq = [defaultdict(set)]
        self.parameter_names = set()
        for partial_domain in self.param_map_seq:
            self.parameter_names.update(partial_domain.keys())
        # If Hashability is a problem, we cound allow for the choice of the
        # defaultdict type (for list, for instance). It would not garantee
        # against colliding domain values, however

    def __repr__(self):
        return "%s(param_map_seq=%s)" % (self.__class__.__name__,
                                         repr(self.param_map_seq))

    def __str__(self):
        return repr(self)

    def __len__(self):
        domains = defaultdict(set)
        for param_map in self.param_map_seq:
            for name, param_domain in param_map.items():
                domains[name].update(param_domain)
        nb = 1
        for val in domains.values():
            nb *= len(val)
        return nb

    def add_single_values(self, **kwargs):
        """
        kwargs: mapping str -> object
            A mapping where each key is a parameter name and the object is
            domain element.
        """
        parameter_mapping = self.param_map_seq[-1]

        for param_name, param_singleton in kwargs.items():
            if param_name not in self.parameter_names:
                if len(self.param_map_seq) != 1:  # separator free
                    # A parameter cannot be added afterward
                    raise ValueError("New parameter (i.e. '%s') cannot be "
                                     "added after the first separator."
                                     % str(param_name))
                self.parameter_names.add(param_name)
            parameter_mapping[param_name].add(param_singleton)
        return self

    def add_parameters(self, **kwargs):
        """

        kwargs: mapping str -> object
            A mapping where each key is a parameter name and the object is
            either a single domain element or a sequence of domain elements.
            If the domain elements are sequences, use `add_single_values`
            instead.
        """
        for param_name, param_val in kwargs.items():
            values = []
            if isinstance(param_val, str):
                values.append(param_val)
            else:
                try:
                    # Duck typing: is param_val a sequence?
                    values.extend(param_val)
                except TypeError:
                    # Was not a sequence
                    values.append(param_val)
            for val in values:
                self.add_single_values(**{param_name: val})
        return self

    def add_separator(self, **kwargs):
        """
        kwargs: mapping str -> object
            A mapping where each key is a parameter name and the object is
            domain element. This mapping represent the default value that he
            absence of parameter represented before this separator.
        """
        # Note: since we allow for only a singleton for unknown parameters,
        # it will not generate more parameter tuples until that parameter is
        # enlarged. Neither will the order be changed, only the tuple size
        for param_name in kwargs.keys():
            if param_name in self.parameter_names:
                raise ValueError("Parameter '%s' already exists." % param_name)
            else:
                self.parameter_names.add(param_name)

        parameter_mapping = self.param_map_seq[0]
        for param_name, param_singleton in kwargs.items():
            parameter_mapping[param_name].add(param_singleton)

        self.param_map_seq.append(defaultdict(set))
        return self

    def _iter(self):
        # Note: using list and sorting is necessary for reproducibility reasons
        parameter_names = list(self.parameter_names)
        parameter_names.sort()
        domains = []  # list (over the ordered name) of lists (domain values)
        param_map = self.param_map_seq[0]
        for name in parameter_names:
            ls = list(param_map[name])
            ls.sort()
            domains.append(ls)

        for param_tuple in cartesian_product(*domains):
            yield 0, {k: t for k, t in zip(parameter_names, param_tuple)}

        # Invariant: domain is up to date regarding self.param_map_seq[:i]
        # and all the tuples of the domain have been yielded
        for j, param_map in enumerate(self.param_map_seq[1:], 1):
            # Invariant: domain is up to date regarding self.param_map_seq[:i]
            # AND parameter_names[:j] ...
            for i, name in enumerate(parameter_names):
                if name in param_map:
                    # Generate the tuples with the new values of the parameter
                    new_values = [x for x in param_map[name]
                                  if x not in domains[i]]
                    # Domains are expected to be small so this should not be
                    # too heavy, even though it is inefficient

                    new_values.sort()
                    dom_tmp = domains[i]  # Store to restore
                    domains[i] = new_values
                    for param_tuple in cartesian_product(*domains):
                        yield j, {k: t for k, t in
                                  zip(parameter_names, param_tuple)}
                    # Restore the full domain
                    dom_tmp.extend(new_values)
                    domains[i] = dom_tmp

    def __iter__(self):
        for j, param_dict in self._iter():
            yield param_dict

    def get_indices_with(self, **kwargs):
        """
        Yields indices of parameter tuples containing the parameter-values given

        kwargs: mapping str -> set
            A mapping where each key is a parameter name and the set is the
            domain of the parameter
        """
        parameter_names = kwargs.keys()
        for index, param_dict in enumerate(self):
            yield_it = True
            for name in parameter_names:
                if param_dict[name] not in kwargs[name]:
                    yield_it = False
                    break
            if yield_it:
                yield index

    def __getitem__(self, index):
        for i, param_dict in enumerate(self):
            if i == index:
                return param_dict

        raise KeyError("Index %d out of range" % index)


class ConstrainedParameterSet(ParameterSet):
    def __init__(self, param_map_seq=None, filters_seq=None):
        super(ConstrainedParameterSet, self).__init__(param_map_seq)
        if filters_seq is None:
            filters_seq = [{}]
        self.filters_seq = filters_seq
        if len(self.filters_seq) != len(self.param_map_seq):
            raise AttributeError("'param_map_seq' and 'filters_seq' must have "
                                 "the same length")

    def __repr__(self):
        return "{cls}(param_map_seq={pms}, filters_seq={fs})" \
               "".format(cls=self.__class__.__name__,
                         pms=repr(self.param_map_seq),
                         fs=repr(self.filters_seq))

    def add_separator(self, **kwargs):
        super(ConstrainedParameterSet, self).add_separator()
        # Keep all the filters
        self.filters_seq.append({k: v for k, v in self.filters_seq[-1].items()})

    def add_constraints(self, **kwargs):
        """
        Add the constraints. Constraints apply from this stage on, they are not
        retroactive with respect to separators.

        kwargs: mapping str -> callable(**kwargs)
            a named predicate. It takes as input a detupled param tuple
        """
        self.filters_seq[-1].update(kwargs)

    def delete_constraints(self, *args):
        for constraint_name in args:
            del self.filters_seq[-1][constraint_name]

    def _iter(self):
        for j, tuple_dict in super(ConstrainedParameterSet, self)._iter():
            yield_it = True
            for constraint in self.filters_seq[j].values():
                if not constraint(**tuple_dict):
                    yield_it = False
                    break
            if yield_it:
                yield j, tuple_dict

    def __len__(self):
        n = 0
        for _ in self:
            n += 1
        return n


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

    def yield_computations(self, context="n/a", start=0, capacity=None):
        if capacity is None:
            capacity = sys.maxsize

        self.monitor.refresh()
        storage = self.monitor.storage
        storage.init()
        unlaunchable = self.monitor.unlaunchable_computations()

        storage_factory = self.storage_factory

        i = 0
        for j, param_dict in enumerate(self.parameter_set):
            if j < start:
                continue
            if i >= capacity:
                break
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

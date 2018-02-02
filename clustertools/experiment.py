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

<<<<<<< HEAD
from functools import reduce
from six import string_types
from clusterlib.scheduler import submit

from .database import get_storage, load_results
from .notification import (pending_job_update, running_job_update,
                           completed_job_update, aborted_job_update,
                           partial_job_update, critical_job_update, Historic)
from .util import reorder, hashlist
=======
from .storage import PickleStorage
from .state import RunningState, Monitor
>>>>>>> v0.0.3


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
<<<<<<< HEAD
            self.params = params
        if param_seq:
            self.param_seq = [copy(self.params)] + list(param_seq)
            self.params = self.param_seq[-1]
        else:
            self.param_seq = [copy(self.params)]

    def add_params(self, **kwargs):
        for k, v in kwargs.items():
            vp = self.params.get(k)
            if vp is None:
                if len(self.param_seq) > 1:
                    raise ValueError("New keyword (i.e. '%s') cannot be addded "
                                     "after the first barrier" % str(k))
                vp = set()
                self.params[k] = vp
            vps = self.param_seq[-1].get(k)
            if vps is None:
                vps = set()
                self.param_seq[-1][k] = vps
            try:
                if isinstance(v, string_types):
                    raise TypeError
                for vi in v:
                    if not vi in vp:
                        vp.add(vi)
                        vps.add(vi)
            except TypeError:
                if v not in vp:
                    vp.add(v)
                    vps.add(v)
        return self

    def add_separator(self):
        self.param_seq.append({k:set() for k in self.param_seq[0].keys()})
        return self

    def __len__(self):
        nb = 1
        for val in self.params.values():
            nb *= len(val)
        return nb

    def __iter__(self):
        # TODO less memory by factorization
        if len(self.params) == 0:
            yield "Computation-"+self.name+"-0", {}
        else:
            keys = list(self.params.keys())
            keys.sort()
            inc = {k:set() for k in keys}
            seen = set()
            nb = 0
            for params_ in self.param_seq:
                for key, value in params_.items():
                    inc[key].update(value)

                values = []
                for vals in [inc[k] for k in keys]:
                    ls = list(vals)
                    ls.sort()
                    values.append(ls)
                for v in product(*values):
                    tup = tuple(zip(keys, v))
                    params = dict(zip(keys, v))
                    if tup in seen:
                        continue
                    label = "Computation-"+self.name+"-"+str(nb)
                    yield label, params
                    nb += 1
                    seen.add(tup)


    def get_params_for(self, sel):
        index = -1
        name = ""
        try:
            index = int(sel)
            # sel is a int
            if index < 0 or index >= len(self):
                raise KeyError("%d not in the range (0, %d)" % (index,
                                                                len(self)-1))
        except ValueError:
            # sel is a string
            name = sel
        name = name.encode("utf-8")
        for i, (label, param) in enumerate(self):
            if i == index or name == label.encode("utf-8"):
                return label, param
        raise KeyError("Key '%s' not found" % str(sel))

    def get_computations_with(self, **kwargs):
        keys = kwargs.keys()
        for i, (label, params) in enumerate(self):
            yield_it = True
            for key in keys:
                if key not in params:
                    yield_it = False
                    break
                if not params[key] == kwargs[key]:
                    yield_it = False
                    break
            if yield_it:
                yield i, label

    def __getitem__(self, sel):
        return self.get_params_for(sel)
=======
            self.param_map_seq = [defaultdict(set)]
        self.parameter_names = set()
        for partial_domain in self.param_map_seq:
            self.parameter_names.update(partial_domain.keys())
        # If Hashability is a problem, we cound allow for the choice of the
        # defaultdict type (for list, for instance). It would not garantee
        # against colliding domain values, however
>>>>>>> v0.0.3

    def __repr__(self):
        return "%s(param_map_seq=%s)" % (self.__class__.__name__,
                                         repr(self.param_map_seq))

    def __str__(self):
        return repr(self)

<<<<<<< HEAD
    def get_metadata(self):
        d = {}
        for k, v in self.params.items():
            if len(v) == 1:
                d[k] = v[0]
        return d

    def get_domain(self):
        d = {}
        for k, v in self.params.items():
            if len(v) > 1:
                d[k] = v
        return d

    def seen_by(self, n_computations):
        seen = defaultdict(set)
        for i, (_, params) in enumerate(self):
            if i >= n_computations:
                break
            for k, v in params.items():
                seen[k].add(v)
        return seen




def _sort_back(dictionary):
    tmp = [(v, k) for k,v in dictionary.items()]
    tmp.sort()
    return [x for _, x in tmp]


class Hasher(object):
    """
    metrics: iterable of metric_name
    domain: mapping param_name -> iterable of values (axis domain)
    metadata: mapping param_name -> param_val
    """
    def __init__(self, metrics, domain, metadata=None):
        self.metric_inv = {p:i for i, p in enumerate(metrics)}
        self.dom_inv = {}
        last_stride = 1
        self.strides = {}
        for name, vals in domain.items():
            inv = {p:i for i, p in enumerate(vals)}
            self.dom_inv[name] = inv
            self.strides[name] = last_stride
            last_stride *= len(vals)

        self.metric_stride = last_stride
        if metadata is not None:
            for name, val in metadata.items():
                self.strides[name] = 0
                self.dom_inv[name] = {val:0}

    def get_cons_args(self):
        metrics = _sort_back(self.metric_inv)
        metadata = {}
        domain = {}
        for param, domdic in self.dom_inv.items():
            if self.strides[param] == 0:
                metadata[param] = _sort_back(domdic)[0]
            else:
                domain[param] = _sort_back(domdic)
        if len(metadata) == 0:
            metadata = None
        return metrics, domain, metadata

    def __repr__(self):
        metrics, domain, metadata = self.get_cons_args()
        cls_name = self.__class__.__name__
        return "%s(metrics=%s, domain=%s, metadata=%s)" % (cls_name,
                                                           repr(metrics),
                                                           repr(domain),
                                                           repr(metadata))


    def add_metadata(self, **kwargs):
        for k, v in kwargs.items():
            self.strides[k] = 0
            self.dom_inv[k] = {v:0}
=======
    def __len__(self):
        domains = defaultdict(set)
        for param_map in self.param_map_seq:
            for name, param_domain in param_map.items():
                domains[name].update(param_domain)
        nb = 1
        for val in domains.values():
            nb *= len(val)
        return nb
>>>>>>> v0.0.3

    def add_single_values(self, **kwargs):
        """
        kwargs: mapping str -> object
            A mapping where each key is a parameter name and the object is
            domain element.
        """
<<<<<<< HEAD
        if len(params) != len(self.strides):
            raise IndexError("Expecting %d parameters/metadata, got %d" % (len(self.strides), len(params)))
        index = self.metric_inv[metric] * self.metric_stride
        for p, pv in params.items():
            index += (self.strides[p] * self.dom_inv[p][pv])
        return index

    def dehash(self, index):
        res = {}
        # First, find the metric:
        metric_index = index // self.metric_stride
        metrics = _sort_back(self.metric_inv)
        res["metric"] = metrics[metric_index]

        # Then, find the parameters
        index = index % self.metric_stride
        dims = [(v, k) for k,v in self.strides.items()]
        dims.sort(reverse=True)
        for stride, param in dims:
            if stride == 0:
                # We arrived at the metadata
                continue
            dom = _sort_back(self.dom_inv[param])
            p_idx = index // stride
            res[param] = dom[p_idx]
            index = index % stride

        return res



    def __call__(self, metric, params):
        return self.hash(metric, params)



class Result(Mapping):
    """
    parameterss : iterable of mappings param_name -> value
    resultss : iterable of mappings metric_name -> value

    Instance variables
    ------------------
    name: str (default "")
        The experiment name
    metadata: mapping str -> value
        A dictionary containing, for each of the metadatum, the associated value
    domain: mapping str -> iterable of values
        A dictionary containing, for each domain name, the iterable of possible
        values
    parameters: iterable of str
        The name of each axis (with correspind index)
    metrics: iterable of str
        The name of each metric. The metric is the last axis. Each index in that
        axis correspond to a metric in the order of `metrics`
    data: iterable
        The raw data
    hash: :class:`Hasher`
        The hasher to the data
    shape: tuple (of size `len(parameters)+1`)
        The shape of the result cube. The N-1 first axis are linked to the
        parameters and the last one to the metrics
    """


    def __init__(self, parameterss, resultss, exp_name=""):
        param_tmp = {}
        # Build back the parameters domain
        for parameters in parameterss:
            for k, v in parameters.items():
                _set = param_tmp.get(k)
                if _set is None:
                    _set = set()
                    param_tmp[k] = _set
                _set.add(v)
        # Sort metadata from parameters
        metadata = {}
        parameter_list = []
        domain = {}
        for k, v in param_tmp.items():
            ls = [vi for vi in v]
            if len(ls) > 1:
                ls.sort()
                domain[k] = [str(x) for x in ls]
                parameter_list.append(k)
            else:
                metadata[k] = str(ls[0])
        parameter_list.sort()

        # Build back the metric list
        _set = set()
        for res in resultss:
            _set.update(res.keys())
        metrics = list(_set)
        metrics.sort()
        metrics = [str(m) for m in metrics]


        # Allocate the data vector
        shape = []
        for p in parameter_list:
            v = domain[p]
            shape.append(len(v))
        shape.append(len(metrics))
        length = reduce(lambda x,y:x*y, shape, 1)
        data = [None for _ in range(length)]

        # Fill the data vector
        hasher = Hasher(metrics, domain, metadata)
        for params, _metrics in zip(parameterss, resultss):
            for metric_name, val in _metrics.items():
                params_ = {k:str(v) for k,v in params.items()}
                index = hasher(str(metric_name), params_)
                data[index] = val
        datahash = "n/a"

        # Set info
        self.name = exp_name
        self.metadata = metadata
        self.domain = domain
        self.parameters = parameter_list
        self.metrics = metrics
        self.data = data
        self.datahash = datahash
        self.hash = hasher
        self.shape = tuple(shape)

    def compute_data_hash(self):
        self.datahash = hashlist(data)
        return self.datahash

    def size(self):
        return reduce(lambda x,y: x*y, self.shape, 1)

    def full_parameters(self):
        doms = [self.domain[v] for v in self.parameters]
        return [(name, dom) for name, dom in zip(self.parameters, doms)]

    def add_metadata(self, **kwargs):
        self.metadata.update(kwargs)
        self.hash.add_metadata(**kwargs)


    def _get_index_by_name(self, n_dim, value):
        lku = self.metrics
        if n_dim < len(self.shape) - 1:
            lku = self.domain[self.parameters[n_dim]]
        try:
            return lku.index(value)
        except ValueError:
            try:
                # TODO not yet working
                fval = float(value)
                lku2 = [float(x) for x in lku]
                for i, x in lku:
                    try:
                        if float(x) == fval:
                            return i
                    except ValueError:
                        pass
                raise ValueError()
            except ValueError:
                raise KeyError("Name '%s' unknown for dimension %d" % (value, n_dim))

=======
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
>>>>>>> v0.0.3

    def add_parameters(self, **kwargs):
        """

        kwargs: mapping str -> object
            A mapping where each key is a parameter name and the object is
            either a single domain element or a sequence of domain elements.
            If the domain elements are sequences, use `add_single_values`
            instead.
        """
<<<<<<< HEAD
        # ====== Building the list of slices/list (Adapted from NumPy) ======
        # At the end, fixed will be a list of either slice or list of ints
        if not isinstance(index, tuple): index = (index,)
        fixed = []
        length, dims = len(index), len(self.shape)

        if length > dims:
            raise IndexError("Too many indices")

        return_scalar = True
        for i, slice_ in enumerate(index):
            if slice_ is Ellipsis:
                # Ellipsis --> Develop
                fixed.extend([slice(None)] * (dims-length+1))
                length = len(fixed)
                return_scalar = False

            elif isinstance(slice_, (int, long)):
                # Int(/long) --> Build the appropriate slice
                # Wrapping
                if slice_ < 0:
                    slice_ += len(self)
                if slice_ < 0:
                    raise IndexError("Index out of range from dim. %d" % i)
                fixed.append(slice(slice_, slice_+1, 1))
            elif isinstance(slice_, string_types):
                # String --> Get the appropriate int
                idx = self._get_index_by_name(i, slice_)
                fixed.append(slice(idx, idx+1, 1))
            elif isinstance(slice_, slice):
                # Slice --> Lookup in case of strings
                start, stop = slice_.start, slice_.stop
                if isinstance(start, string_types):
                    start = self._get_index_by_name(i, start)
                if isinstance(stop, string_types):
                    stop = self._get_index_by_name(i, stop) + 1
                fixed.append(slice(start, stop, slice_.step))
                return_scalar = False
            else:
                try:
                    # List of str/int --> Lookup strings
                    slice2 = []
                    for idx in slice_:
                        if isinstance(idx, string_types):
                            slice2.append(self._get_index_by_name(i, idx))
                        else:
                            # Wrapping
                            if idx < 0:
                                idx += len(self)
                            if idx < 0:
                                raise IndexError("Index out of range from dim. %d" % i)
                            slice2.append(idx)
                    fixed.append(slice2)
                except TypeError:
                    # Else ?
                    fixed.append(slice_)
                return_scalar = False
        index = tuple(fixed)
        if len(index) < dims:
            index += (slice(None),) * (dims-len(index))
            return_scalar = False


        # ====== Building the return ======
        # +-> Checking if the slice is whole
        same_obj = True
        for i, idx in enumerate(index):
            tmp = self.domain[self.parameters[i]] if i < dims-1 else self.metrics
            if isinstance(idx, slice):
                # In case of slice
                same_obj = same_obj and (idx.start is None or idx.start == 0)
                same_obj = same_obj and (idx.stop is None or (0 < len(tmp) < idx.stop))
                same_obj = same_obj and (idx.step is None or idx.step == 1)
            else:
                # In case of list
                same_obj = same_obj and (idx == tmp)
        if same_obj:
            return self

        p_slices, m_slice = index[:-1], index[-1]
        # +-> Looking for a scalar
        # +--> We are sure to have a list of slices of one item
        if return_scalar:
            metric = self.metrics[m_slice.start]
            # We need to include the metadata for the hasher
            params = {k:v for k,v in self.metadata.items()}
            for i, slc in enumerate(p_slices):
                p_name = self.parameters[i]
                vals = self.domain[p_name]
                params[p_name] = vals[slc.start]
            return self.data[self.hash(metric, params)]

        # +-> Looking for a sliced Result
        clone = copy(self)
        # Deepcopy of the dict which will be modified in place
        clone.metadata = deepcopy(self.metadata)
        clone.domain = deepcopy(self.domain)

        # +---> Processing the parameters
        shape = []
        for i, slc in enumerate(p_slices):
            param_name = self.parameters[i]
            vals = self.domain[param_name]
            if isinstance(slc, slice):
                # In case of slice
                newvals = vals[slc]
            else:
                # In case of list
                newvals = list(reorder(vals, slc, in_place=False))
            if len(newvals) == 0:
                pass   # ??
            if len(newvals) == 1:
                # Must shift from domain/param into metadata and remove dim
                clone.metadata[param_name] = newvals[0]
                clone.parameters = [x for x in clone.parameters if x != param_name]
                del clone.domain[param_name]
=======
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
>>>>>>> v0.0.3
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

<<<<<<< HEAD
    def iteritems(self):
        """
        Yields pairs (params, metrics) in the order of this `Result`
        """
        p_gen = product(*[self.domain[p] for p in self.parameters])
        for params in p_gen:
            p_dict = {k:v for k,v in zip(self.parameters, params)}
            p_dict.update(self.metadata)
            idx = [self.hash(m, p_dict) for m in self.metrics]
            data = tuple(self.data[x] for x in idx)
            yield params, data

    def in_domain(self):
        idom = []
        for params, metrics in self.items():
            append = True
            for i, metric in enumerate(metrics):
                if metric is None:
                    append = False
                    break
            if append:
                p_dict = {k:v for v,k in zip(params, self.parameters)}
                idom.append(p_dict)
        return idom


    def out_of_domain(self):
        ood = []
        for params, metrics in self.items():
            for i, metric in enumerate(metrics):
                if metric is None:
                    p_dict = {k:v for v,k in zip(params, self.parameters)}
                    ood.append((p_dict, self.metrics[i]))
        return ood

    def _missing_ratio(self, ood=None):
        if ood is None:
            ood = self.out_of_domain()
        return float(len(ood))/self.size()

    def _some_miss_vs_all_there(self, ood=None):
        if ood is None:
            ood = self.out_of_domain()
        sets = {k:set() for k in self.parameters}
        for tup in ood:
            for param in self.parameters:
                miss_dict = tup[0]
                sets[param].add(miss_dict[param])
        some_missings = {}
        all_there = {}
        # Same order as in domain
        for param, domls in self.domain.items():
            some_missings[param] = [v for v in domls if v in sets[param]]
            all_there[param] = [v for v in domls if v not in sets[param]]
        return some_missings, all_there


    def diagnose(self):
        ood = self.out_of_domain()
        some_missings, all_there = self._some_miss_vs_all_there(ood)

        diagnosis = {
            "Missing ratio":self._missing_ratio(ood),
            "At least one missing": some_missings,
            "All there": all_there
        }
        return diagnosis

    def maximal_hypercube(self, metric=None):
        cube = self if metric is None else self(metric=metric)
        _, all_there = cube._some_miss_vs_all_there()
        max_key, max_len = None, -1
        for k,v in all_there.items():
            if len(v) > max_len:
                max_len = len(v)
                max_key = k
        return cube(**{max_key:all_there[max_key]})


    def minimal_hypercube(self, metric=None):
        cube = self if metric is None else self(metric=metric)
        _, all_there = cube._some_miss_vs_all_there()
        slicing = {k:v for k,v in all_there.items() if len(v) > 0}
        return cube(**slicing)
=======
    def _iter(self):
        for j, tuple_dict in super(ConstrainedParameterSet, self)._iter():
            yield_it = True
            for constraint in self.filters_seq[j].values():
                if not constraint(**tuple_dict):
                    yield_it = False
                    break
            if yield_it:
                yield j, tuple_dict
>>>>>>> v0.0.3

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


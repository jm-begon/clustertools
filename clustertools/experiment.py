# -*- coding: utf-8 -*-

"""
Module :mod:`experiment` is a set of functions and classes to build, run and
monitor experiments

Restriction
-----------
Experiment names should always elligible file names.
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

import sys, os
import subprocess
from subprocess import CalledProcessError
import logging
from itertools import product
from copy import copy, deepcopy
from collections import Mapping

from clusterlib.scheduler import submit

from .database import get_storage, load_experiment_names, load_results
from .notification import (pending_job_update, running_job_update,
                           completed_job_update, aborted_job_update,
                           partial_job_update, critical_job_update, Historic)
from .util import encode_kwargs, reorder, hashlist

__EXP_NAME__ = "Experiment"
__PARAMETERS__ = "Parameters"
__RESULTS__ = "Results"


class Computation(object):

    def __init__(self, exp_name, comp_name, overwrite=True):
        self.exp_name = exp_name
        self.comp_name = comp_name
        self.overwrite = overwrite
        self.storage = get_storage(self.exp_name)

    def _save(self, result):
        self.storage.save_result(self.comp_name, result, self.overwrite)

    def run(self, **parameters):
        pass

    def __call__(self, **parameters):
        start = running_job_update(self.exp_name, self.comp_name)
        try:
            result = {
                self.comp_name: {
                    __EXP_NAME__: self.exp_name,
                    __PARAMETERS__: parameters,
                    __RESULTS__: self.run(**parameters)
                }
            }
            critical_job_update(self.exp_name, self.comp_name, start)
            self._save(result)
            completed_job_update(self.exp_name, self.comp_name, start)
        except Exception as excep:
            aborted_job_update(self.exp_name, self.comp_name, start, excep)
            raise

class PartialComputation(Computation):
    """
    Expect the run method to be a generator
    """
    def __call__(self, **parameters):
        start = running_job_update(self.exp_name, self.comp_name)
        try:
            for partial_result in self.run(**parameters):
                result = {
                    self.comp_name: {
                        __EXP_NAME__: self.exp_name,
                        __PARAMETERS__: parameters,
                        __RESULTS__: partial_result
                    }
                }
                critical_job_update(self.exp_name, self.comp_name, start)
                self._save(result)
                partial_job_update(self.exp_name, self.comp_name, start)
            completed_job_update(self.exp_name, self.comp_name, start)
        except Exception as excep:
            aborted_job_update(self.exp_name, self.comp_name, start, excep)
            raise

    def load_partial(self):
        """return a dict"""
        return self.storage.load_result(self.comp_name)


class Experiment(object):
    """
    param_seq : list of dict
    """
    def __init__(self, name, params=None, param_seq=None):
        self.name = name
        if not params:
            self.params = {}
        else:
            self.params = params
        if param_seq:
            self.param_seq = [copy(self.params)] + list(param_seq)
            self.params = self.param_seq[-1]
        else:
            self.param_seq = [copy(self.params)]

    def add_params(self, **kwargs):
        for k, v in kwargs.iteritems():
            vp = self.params.get(k)
            if vp is None:
                if len(self.param_seq) > 1:
                    raise ValueError("New keyword (i.e. '%s') cannot be addded after the first barrier" % str(k))
                vp = set()
                self.params[k] = vp
            vps = self.param_seq[-1].get(k)
            if vps is None:
                vps = set()
                self.param_seq[-1][k] = vps
            try:
                if isinstance(v, basestring):
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
            keys = self.params.keys()
            keys.sort()
            inc = {k:set() for k in keys}
            seen = set()
            nb = 0
            for params_ in self.param_seq:
                for key, value in params_.iteritems():
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
                raise KeyError("%d not in the range [0, %d]" %
                                    (index, len(self)-1))
        except ValueError:
            # sel is a string
            name = sel
        name = name.encode("utf-8")
        for i, (label, param) in enumerate(self):
            if i == index or name == label.encode("utf-8"):
                return label, param
        raise KeyError("Key '%s' not found" % str(sel))

    def __getitem__(self, sel):
        return self.get_params_for(sel)

    def __repr__(self):
        return "%s(name='%s', param_seq=%s)" % (self.__class__.__name__, self.name,
                                             repr(self.param_seq))

    def __str__(self):
        return repr(self)


    def get_metadata(self):
        d = {}
        for k, v in self.params.iteritems():
            if len(v) == 1:
                d[k] = v[0]
        return d

    def get_domain(self):
        d = {}
        for k, v in self.params.iteritems():
            if len(v) > 1:
                d[k] = v
        return d


def _sort_back(dictionary):
    tmp = [(v, k) for k,v in dictionary.iteritems()]
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
        for name, vals in domain.iteritems():
            inv = {p:i for i, p in enumerate(vals)}
            self.dom_inv[name] = inv
            self.strides[name] = last_stride
            last_stride *= len(vals)

        self.metric_stride = last_stride
        if metadata is not None:
            for name, val in metadata.iteritems():
                self.strides[name] = 0
                self.dom_inv[name] = {val:0}

    def get_cons_args(self):
        metrics = _sort_back(self.metric_inv)
        metadata = {}
        domain = {}
        for param, domdic in self.dom_inv.iteritems():
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
        for k, v in kwargs.iteritems():
            self.strides[k] = 0
            self.dom_inv[k] = {v:0}

    def hash(self, metric, params):
        """
        metric: str
            A metric name
        params: mapping str -> value
            A mapping from parameter names to values of their domain
        """
        if len(params) != len(self.strides):
            raise IndexError("Expecting %d parameters/metadata, got %d" % (len(self.strides), len(params)))
        index = self.metric_inv[metric] * self.metric_stride
        for p, pv in params.iteritems():
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
        dims = [(v, k) for k,v in self.strides.iteritems()]
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
            for k, v in parameters.iteritems():
                _set = param_tmp.get(k)
                if _set is None:
                    _set = set()
                    param_tmp[k] = _set
                _set.add(v)
        # Sort metadata from parameters
        metadata = {}
        parameter_list = []
        domain = {}
        for k, v in param_tmp.iteritems():
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
        data = [None for _ in xrange(length)]

        # Fill the data vector
        hasher = Hasher(metrics, domain, metadata)
        for params, _metrics in zip(parameterss, resultss):
            for metric_name, val in _metrics.iteritems():
                params_ = {k:str(v) for k,v in params.iteritems()}
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


    def __getitem__(self, index):
        """
        Index: singleton, cf self[index, ...]
        Index: tuple -> for each elem
            elem: int (= index of param value or metric)
                Select only that value/metric
            elem: str
                Same as int but will perform a lookup to get the index
            elem: slice of int
                Slice along those values/metrics
            elem: slice of str
                Same as slice of int but will perform a lookup to get the indices
            elem: iterable of int
                Will select only those values/metrics
            elem: iterable of str
                Same as iterable of int but will perform a lookup to get the indices
        If all indices are ints, return the value and not a view of the Result

        """
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
            elif isinstance(slice_, basestring):
                # String --> Get the appropriate int
                idx = self._get_index_by_name(i, slice_)
                fixed.append(slice(idx, idx+1, 1))
            elif isinstance(slice_, slice):
                # Slice --> Lookup in case of strings
                start, stop = slice_.start, slice_.stop
                if isinstance(start, basestring):
                    start = self._get_index_by_name(i, start)
                if isinstance(stop, basestring):
                    stop = self._get_index_by_name(i, stop) + 1
                fixed.append(slice(start, stop, slice_.step))
                return_scalar = False
            else:
                try:
                    # List of str/int --> Lookup strings
                    slice2 = []
                    for idx in slice_:
                        if isinstance(idx, basestring):
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
            params = {k:v for k,v in self.metadata.iteritems()}
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
            else:
                # Must update the domain
                clone.domain[param_name] = newvals
                shape.append(len(newvals))

        # +---> Processing the metrics
        if isinstance(m_slice, slice):
            # In case of slice
            newmetrics = self.metrics[m_slice]
        else:
            # In case of list
            newmetrics = list(reorder(self.metrics, m_slice, in_place=False))
        if len(newmetrics) == 0:
            pass   # ??
        clone.metrics = newmetrics
        shape.append(len(newmetrics))
        clone.shape = tuple(shape)
        return clone


    def __iter__(self):
        if len(self.parameters) == 0:
            for m in range(len(self.metrics)):
                # If there are only metrics, yield their values not
                # a Result view
                yield self[m]
        else:
            for v in range(len(self.domain[self.parameters[0]])):
                yield self[v, ...]

    def __len__(self):
        return self.shape[0]

    def __call__(self, metric=None, **kwargs):
        if len(kwargs) == 0 and metric is None:
            return self

        # Computing the slices
        slices = []
        for p in self.parameters:
            v = kwargs.get(p)
            if v is None:
                v = slice(None)
            slices.append(v)

        for k in kwargs.keys():
            if k not in self.parameters:
                raise IndexError("Parameter '%s' does not exist"%str(k))

        if metric is None:
            metric = slice(None)
        slices.append(metric)

        return self[tuple(slices)]



    def __getslice__(self, start, stop) :
        """This solves a subtle bug, where __getitem__ is not called, and all
        the dimensional checking not done, when a slice of only the first
        dimension is taken, e.g. a[1:3]. From the Python docs:
       Deprecated since version 2.0: Support slice objects as parameters
       to the __getitem__() method. (However, built-in types in CPython
       currently still implement __getslice__(). Therefore, you have to
       override it in derived classes when implementing slicing.)
        """
        return self.__getitem__(slice(start, stop))

    def numpify(self, squeeze=False):
        import numpy as np
        if len(self.parameters) == 0:
            # Only metrics, everything is in metadata
            return np.array([self.data[self.hash(m, self.metadata)]
                    for m in self.metrics])

        arr = np.array([arr.numpify() for arr in self])
        if squeeze and arr.shape[-1] == 1:
            arr = arr.squeeze()
        return arr

    def reorder_parameters(self, *args):
        order = []
        for x in args:
            if isinstance(x, (int, long)):
                order.append(x)
            else:
                # lookup
                order.append(self.parameters.index(x))
        diff = [i for i in range(len(self.parameters)) if i not in order]
        order.extend(diff)
        tmps = [self.parameters[i] for i in order]
        for i, param in enumerate(tmps):
            self.parameters[i] = param

    def iter_dimensions(self, *dimensions):
        if len(dimensions) == 0:
            yield (), self
        else:
            dim = dimensions[0]
            if dim in self.metadata:
                for values, dbi in self.iter_dimensions(*dimensions[1:]):
                    new_values = tuple([self.metadata[dim]] + list(values))
                    yield new_values, dbi
            else:
                for dim_value in self.domain[dim]:
                    # Slicing is fast, no need to cache intermediate result
                    res_tmp = self(**{dim:dim_value})
                    for values, dbi in res_tmp.iter_dimensions(*dimensions[1:]):

                        new_values = tuple([dim_value] + list(values))
                        yield new_values, dbi



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
        for params, metrics in self.iteritems():
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
        for params, metrics in self.iteritems():
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
        for param, domls in self.domain.iteritems():
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
        for k,v in all_there.iteritems():
            if len(v) > max_len:
                max_len = len(v)
                max_key = k
        return cube(**{max_key:all_there[max_key]})


    def minimal_hypercube(self, metric=None):
        cube = self if metric is None else self(metric=metric)
        _, all_there = cube._some_miss_vs_all_there()
        slicing = {k:v for k,v in all_there.iteritems() if len(v) > 0}
        return cube(**slicing)


    def __str__(self):
        try:
            val = "Values:\n"+str(self.numpify())
        except:
            val = "Hash of data: \t"+self.datahash
        return """Results of '%s':
=====================
Metadata: \t%s
Parameters: \t%s
Domain: \t%s
Metrics: \t%s
Shape: \t%s
%s""" % (self.name, str(self.metadata), str(self.parameters), str(self.domain),
         str(self.metrics), str(self.shape), val)

    def __repr__(self):
        return "%s(name='%s', metadata=%s, parameters=%s, domain=%s," \
               " metrics=%s, data='%s')" % (self.__class__.__name__, self.name, \
               str(self.metadata), str(self.parameters), str(self.domain),
               str(self.metrics), self.datahash)



    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        same = True
        same = same and (self.name == other.name)
        same = same and (self.metadata == other.metadata)
        same = same and (self.parameters == other.parameters)
        same = same and (self.domain == other.domain)
        same = same and (self.metrics == other.metrics)
        same = same and (self.data == other.data)
        return same


    def __ne__(self, other):
        return not self.__eq__(other)




def build_result_cube(exp_name, *exp_names):
    exps = [exp_name]
    if len(exp_names) > 0:
        exps = exps + list(exp_names)
    parameterss = []
    resultss = []
    for exp in exps:
        result = load_results(exp)
        for d in result.values():
            parameterss.append(d[__PARAMETERS__])
            resultss.append(d[__RESULTS__])
    return Result(parameterss, resultss, exp_name)




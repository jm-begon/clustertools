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

from .database import save_result, save_experiment, load_results
from .notification import (pending_job_update, running_job_update,
                           completed_job_update, aborted_job_update, Historic)
from .util import encode_kwargs

__EXP_NAME__ = "Experiment"
__PARAMETERS__ = "Parameters"
__RESULTS__ = "Results"


class Computation(object):

    def __init__(self, exp_name, comp_name, overwrite=True):
        self.exp_name = exp_name
        self.comp_name = comp_name
        self.overwrite = overwrite

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
            save_result(self.exp_name, result)
            completed_job_update(self.exp_name, self.comp_name, start)
        except Exception as excep:
            aborted_job_update(self.exp_name, self.comp_name, start, excep)
            raise




class Experiment(object):

    def __init__(self, name, params=None):
        self.name = name
        if not params:
            self.params = {}
        else:
            self.params = params

    def add_params(self, **kwargs):
        for k, v in kwargs.iteritems():
            vp = self.params.get(k)
            if vp is None:
                vp = []
                self.params[k] = vp
            try:
                if isinstance(v, basestring):
                    raise TypeError
                for vi in v:
                    vp.append(vi)
            except TypeError:
                vp.append(v)
            finally:
                vp.sort()

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

    def __len__(self):
        nb = 1
        for val in self.params.values():
            nb *= len(val)
        return nb

    def __iter__(self):
        if len(self.params) == 0:
            yield "Computation-"+self.name+"-0", self.serialize({})
        else:
            keys = self.params.keys()
            keys.sort()
            values = [self.params[k] for k in keys]
            for i, v in enumerate(product(*values)):
                params = dict(zip(keys, v))
                label = "Computation-"+self.name+"-"+str(i)
                yield label, params

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
        for i, (label, param) in enumerate(self):
            if i == index or name.encode("utf-8") == label.encode("utf-8"):
                return label, param
        raise KeyError("Key '%s' not found" % str(sel))

    def __getitem__(self, sel):
        return self.get_params_for(sel)

    def __str__(self):
        return "Experiment '%s': %s" % (self.name, str(self.params))


def build_result_cube(exp_name):
    res = load_results(exp_name)
    parameterss = []
    resultss = []
    for d in res.values():
        parameterss.append(d[__PARAMETERS__])
        resultss.append(d[__RESULTS__])
    return Result(parameterss, resultss, exp_name)


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

    def hash(self, metric, params):
        """
        metric: str
            A metric name
        params: mapping str -> value
            A mapping from parameter names to values of their domain
        """
        index = self.metric_inv[metric] * self.metric_stride
        for p, pv in params.iteritems():
            index += (self.strides[p] * self.dom_inv[p][pv])
        return index

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
                domain[k] = ls
                parameter_list.append(k)
            else:
                metadata[k] = ls[0]
        parameter_list.sort()

        # Build back the metric list
        _set = set()
        for res in resultss:
            _set.update(res.keys())
        metrics = list(_set)
        metrics.sort()


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
                index = hasher(metric_name, params)
                data[index] = val

        # Set info
        self.name = exp_name
        self.metadata = metadata
        self.domain = domain
        self.parameters = parameter_list
        self.metrics = metrics
        self.data = data
        self.hash = hasher
        self.shape = tuple(shape)

    def size(self):
        return reduce(lambda x,y: x*y, self.shape, 1)

    def _get_index_by_name(self, n_dim, value):
        lku = self.metrics
        if n_dim < len(self.shape) - 1:
            lku = self.domain[self.parameters[n_dim]]
        try:
            return lku.index(value)
        except ValueError:
            raise KeyError("Name '%s' for dimension %d" % (value, n_dim))


    def __getitem__(self, index):
        # ====== Building the list of slices (Adapted from NumPy) ======
        if not isinstance(index, tuple): index = (index,)
        fixed = []
        length, dims = len(index), len(self.shape)

        if length > dims:
            raise IndexError("Too many indices")

        return_scalar = True
        for i, slice_ in enumerate(index):
            if slice_ is Ellipsis:
                fixed.extend([slice(None)] * (dims-length+1))
                length = len(fixed)
                return_scalar = False

            elif isinstance(slice_, (int, long)):
                fixed.append(slice(slice_, slice_+1, 1))
            elif isinstance(slice_, basestring):
                # Indexing by a parameter value
                idx = self._get_index_by_name(i, slice_)
                fixed.append(slice(idx, idx+1, 1))
            elif isinstance(slice_, slice):
                start, stop = slice_.start, slice_.stop
                if isinstance(start, basestring):
                    start = self._get_index_by_name(i, start)
                if isinstance(stop, basestring):
                    stop = self._get_index_by_name(i, stop) + 1
                fixed.append(slice(start, stop, slice_.step))
                return_scalar = False
            else:
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
            same_obj = (idx.start is None or idx.start == 0) and same_obj
            same_obj = (idx.stop is None or (0 < len(tmp) < idx.stop)) and same_obj
            same_obj = (idx.step is None or idx.step == 1) and same_obj
        if same_obj:
            return self

        p_slices, m_slice = index[:-1], index[-1]
        # +-> Looking for a scalar
        if return_scalar:
            metric = self.metrics[m_slice.start]
            params = {}
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
            newvals = vals[slc]
            if len(newvals) == 0:
                pass   # ??
            if len(newvals) == 1:
                # Must shift from domain/param into metadata and remove dim
                clone.metadata[param_name] = newvals[0]
                clone.parameters = [x for x in clone.parameters if x != param_name]
                del clone.domain[param_name]
            else:
                # Must update the domain (order of the domain value
                # is still respected)
                clone.domain[param_name] = newvals
                shape.append(len(newvals))

        # +---> Processing the metrics
        newmetrics = self.metrics[m_slice]
        if len(newmetrics) == 0:
            pass   # ??
        clone.metrics = newmetrics
        shape.append(len(newmetrics))
        clone.shape = tuple(shape)
        return clone


    def __iter__(self):
        if len(self.parameters) == 0:
            for m in range(len(self.metrics)):
                yield self[..., m]
        for v in range(len(self.domain[self.parameters[0]])):
            yield self[v, ...]

    def __len__(self):
        return self.shape[0]

    def __call__(self, metric=None, **kwargs):
        if len(kwargs) == 0 and metric is None:
            return self

        # # Input checks
        # if isinstance(metric, basestring) and metric not in self.metrics:
        #     raise KeyError("Metric '%s' does not exist" % str(metric))
        # paramset = frozenset(self.parameters)
        # for k in kwargs.keys():
        #     if k not in paramset:
        #         raise KeyError("Parameter '%s' does not exist" % str(k))

        # Computing the slices
        slices = []
        for p in self.parameters:
            v = kwargs.get(p)
            if v is None:
                v = slice(None)
            slices.append(v)

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

    def numpify(self):
        import numpy as np
        if len(self.parameters) == 0:
            # Only metrics, everything is in metadata
            return np.array([self.data[self.hash(m, self.metadata)]
                    for m in self.metrics])

        return np.array([arr.numpify() for arr in self])





def yield_not_done_computation(experiment, user=os.environ["USER"]):
    historic = Historic(experiment.name, user)
    for comp_name, param in experiment:
        if historic.is_launchable(comp_name):
            yield comp_name, param



def run_experiment(experiment, script_path, build_script=submit,
                   overwrite=True, user=os.environ["USER"],
                   serialize=encode_kwargs):
    logger = logging.getLogger("clustertools")
    exp_name = experiment.name

    save_experiment(experiment, overwrite)

    i = -1
    for job_name, param in yield_not_done_computation(experiment, user):
        i += 1
        job_command = '%s %s "%s" "%s" "%s"' % (sys.executable, script_path,
                                               exp_name, job_name,
                                               serialize(param))

        script = build_script(job_command, job_name=job_name)
        logger.debug("Script:\n%s" % script)

        start = pending_job_update(exp_name, job_name)
        try:
            output = subprocess.check_output(script, shell=True)
            logger.debug("Output:\n%s" % output)
        except CalledProcessError as exception:
            aborted_job_update(exp_name, job_name, start, exception)
            logger.error("Error launching job '%s': %s" % (job_name,
                exception.message), exc_info=True)

    logger.info("Experiment '%s': %d computation(s)" % (exp_name, (i+1)))


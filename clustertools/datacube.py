# -*- coding: utf-8 -*-

from functools import reduce
from itertools import product
from copy import copy, deepcopy
from collections import Mapping
from .util import reorder, hashlist, deprecated

from .storage import PickleStorage

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


class Hasher(object):
    """
    metrics: iterable of metric_name
    domain: mapping param_name -> iterable of values (axis domain)
    metadata: mapping param_name -> param_val
    """
    @classmethod
    def sort_back(cls, dictionary):
        tmp = [(v, k) for k, v in dictionary.items()]
        tmp.sort()
        return [x for _, x in tmp]

    def __init__(self, metrics, domain, metadata=None):
        self.metric_inv = {p: i for i, p in enumerate(metrics)}
        self.dom_inv = {}
        last_stride = 1
        self.strides = {}
        for name, vals in domain.items():
            if len(vals) == 0:
                raise ValueError("Domain of '{}' is empty. "
                                 "If it is not useful remove it.".format(name))
            inv = {p: i for i, p in enumerate(vals)}
            self.dom_inv[name] = inv
            self.strides[name] = last_stride
            last_stride *= len(vals)

        self.metric_stride = last_stride
        if metadata is not None:
            for name, val in metadata.items():
                self.strides[name] = 0
                self.dom_inv[name] = {val: 0}

    def get_cons_args(self):
        metrics = Hasher.sort_back(self.metric_inv)
        metadata = {}
        domain = {}
        for param, domdic in self.dom_inv.items():
            if self.strides[param] == 0:
                metadata[param] = Hasher.sort_back(domdic)[0]
            else:
                domain[param] = Hasher.sort_back(domdic)
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
        for p, pv in params.items():
            index += (self.strides[p] * self.dom_inv[p][pv])
        return index

    def dehash(self, index):
        res = {}
        # First, find the metric:
        metric_index = index // self.metric_stride
        metrics = Hasher.sort_back(self.metric_inv)
        res["metric"] = metrics[metric_index]

        # Then, find the parameters
        index = index % self.metric_stride
        dims = [(v, k) for k,v in self.strides.items()]
        dims.sort(reverse=True)
        for stride, param in dims:
            if stride == 0:
                # We arrived at the metadata
                continue
            dom = Hasher.sort_back(self.dom_inv[param])
            p_idx = index // stride
            res[param] = dom[p_idx]
            index = index % stride

        return res

    def __call__(self, metric, params):
        return self.hash(metric, params)


class Datacube(Mapping):
    """
    parameters_ls : iterable of mappings param_name -> value
        The parameters of the experiment. The indexing must be coherent with
        `results_ls`

    results_ls: iterable of mappings metric_name -> value
        The metric of the experiment. The indexing must be coherent with
        `parameters_ls`

    exp_name: str (default: '')
        The name of the experiment

    force: boolean (default: True)
        Whether to force the building of the cube. If False, will raise
        exception for ill-formed cube (e.g. a parameter with no value). If True,
        will try to enforce the building of the cube -- possibly by droping some
        parameters

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
        The name of each axis (with corresponding index)
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
    def __init__(self, parameters_ls, results_ls, exp_name="", force=True,
                 autopacking=False):
        self.autopacking = autopacking
        param_tmp = {}
        # Build back the parameters domain
        if not force and len(parameters_ls) == 0:
            raise ValueError("Empty cube. Use 'force=True' to ignore this "
                             "issue.")
        for parameters in parameters_ls:
            if not force and len(parameters) == 0:
                raise ValueError("Parameter '{}' has an empty domain. "
                                 "Use 'force=True' to ignore this issue."
                                 "".format(name))
            for name, v in parameters.items():
                _set = param_tmp.get(name)
                if _set is None:
                    _set = set()
                    param_tmp[name] = _set
                _set.add(v)
        # Sort metadata from parameters
        metadata = {}
        parameter_list = []
        domain = {}
        for name, v in param_tmp.items():
            ls = [vi for vi in v]
            if len(ls) > 1:
                ls.sort()
                domain[name] = [str(x) for x in ls]
                parameter_list.append(name)
            elif len(ls) == 1:
                metadata[name] = str(ls[0])
            else:
                # len(ls) <= 0: This should be handled by the previous stage
                if not force:
                    raise ValueError("Parameter '{}' has an empty domain. If "
                                     "it is not useful, remove it".format(name))
                # else: drop that axis
        parameter_list.sort()

        # Build back the metric list
        _set = set()
        for res in results_ls:
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
        for params, _metrics in zip(parameters_ls, results_ls):
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
        self.datahash = hashlist(self.data)
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

            elif isinstance(slice_, int):
                # Int(/long) --> Build the appropriate slice
                # Wrapping
                if slice_ < 0:
                    slice_ += len(self)
                if slice_ < 0:
                    raise IndexError("Index out of range from dim. %d" % i)
                fixed.append(slice(slice_, slice_+1, 1))
            elif isinstance(slice_, str):
                # String --> Get the appropriate int
                idx = self._get_index_by_name(i, slice_)
                fixed.append(slice(idx, idx+1, 1))
            elif isinstance(slice_, slice):
                # Slice --> Lookup in case of strings
                start, stop = slice_.start, slice_.stop
                if isinstance(start, str):
                    start = self._get_index_by_name(i, start)
                if isinstance(stop, str):
                    stop = self._get_index_by_name(i, stop) + 1
                fixed.append(slice(start, stop, slice_.step))
                return_scalar = False
            else:
                try:
                    # List of str/int --> Lookup strings
                    slice2 = []
                    for idx in slice_:
                        if isinstance(idx, str):
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

        # Checking the kwargs are known
        filtered = {}
        for k, v in kwargs.items():
            if k in self.parameters:
                filtered[k] = v
            elif k in self.metadata and v == self.metadata[k]:
                filtered[k] = None
            else:
                raise IndexError("Parameter '{}' does not exist".format(k))

        # Computing the slices
        slices = []
        for p in self.parameters:
            v = filtered.get(p)
            if v is None:
                v = slice(None)
            slices.append(v)

        if metric is None:
            metric = slice(None)
        slices.append(metric)

        res = self[tuple(slices)]
        return res if (not self.autopacking or not isinstance(res, Datacube)) \
            else res.minimal_hypercube()

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

    def numpyfy(self, squeeze=True):
        import numpy as np
        if len(self.parameters) == 0:
            # Only metrics, everything is in metadata
            return np.array([self.data[self.hash(m, self.metadata)]
                             for m in self.metrics])

        arr = np.array([arr.numpyfy() for arr in self])
        if squeeze and arr.shape[-1] == 1:
            arr = arr.squeeze()
        return arr

    @deprecated
    def numpify(self, squeeze=False):
        return self.numpyfy(squeeze)

    def reorder_parameters(self, *args):
        order = []
        for x in args:
            if isinstance(x, int):
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

    @deprecated
    def iteritems(self):
        return self.items()

    def items(self):
        """
        Yields pairs (params, metrics) in the order of this `Result`
        """
        p_gen = product(*[self.domain[p] for p in self.parameters])
        for params in p_gen:
            p_dict = {k: v for k, v in zip(self.parameters, params)}
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
        size = self.size()
        if size == 0:
            raise AttributeError("Cannot do this operation: the cube is empty")
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
            "Missing ratio": self._missing_ratio(ood),
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
        some_missings, all_there = cube._some_miss_vs_all_there()
        if sum([len(x) for x in some_missings.values()]) == 0:
            return self
        slicing = {k:v for k,v in all_there.items() if len(v) > 0}
        return cube(**slicing)

    def __str__(self):
        return repr(self)

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


@deprecated
def build_result_cube(exp_name):
    return build_datacube(exp_name)


def build_datacube(exp_name, storage_factory=PickleStorage, force=True,
                   autopacking=False, **default_meta):
    """
    default_meta: mapping str -> str
        The (potientially) missing metadata
    """
    storage = storage_factory(experiment_name=exp_name)
    parameters_ls, results_ls = storage.load_params_and_results(**default_meta)
    return Datacube(parameters_ls, results_ls, exp_name, force=force,
                    autopacking=autopacking)


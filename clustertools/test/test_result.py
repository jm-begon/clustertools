# -*- coding: utf-8 -*-

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


from nose.tools import assert_dict_equal
from nose.tools import assert_equal
from nose.tools import assert_not_equal
from nose.tools import assert_in


from clustertools import Result, Hasher

def basic():
    res = {u'Computation-basic-0': {'Experiment': 'basic',
            'Parameters': {u'w': 5, u'x': 1, u'z': 4},
            'Results': {'f1': 2, 'f2': 9}},
            u'Computation-basic-1': {'Experiment': 'basic',
            'Parameters': {u'w': 6, u'x': 1, u'z': 4},
            'Results': {'f1': 2, 'f2': 10}},
            u'Computation-basic-2': {'Experiment': 'basic',
            'Parameters': {u'w': 5, u'x': 2, u'z': 4},
            'Results': {'f1': 4, 'f2': 9}},
            u'Computation-basic-3': {'Experiment': 'basic',
            'Parameters': {u'w': 6, u'x': 2, u'z': 4},
            'Results': {'f1': 4, 'f2': 10}},
            u'Computation-basic-4': {'Experiment': 'basic',
            'Parameters': {u'w': 5, u'x': 3, u'z': 4},
            'Results': {'f1': 6, 'f2': 9}},
            u'Computation-basic-5': {'Experiment': 'basic',
            'Parameters': {u'w': 6, u'x': 3, u'z': 4},
            'Results': {'f1': 6, 'f2': 10}}}

    # Notice the ordering
    domain = {'x':[1, 2, 3], 'w':[5, 6]}
    metadata = {'z':4}
    parameters = ["x", "w"]
    parameters.sort()
    metrics = ["f1", "f2"]
    metrics.sort()
    exp_name = "basic"
    return exp_name, metadata, parameters, domain, metrics, res

def build_cube(exp_name, res):
    parameterss = []
    resultss = []
    for d in res.values():
        parameterss.append(d["Parameters"])
        resultss.append(d["Results"])
    return Result(parameterss, resultss, exp_name)


def test_info():
    name, metadata, params, dom, metrics, d = basic()
    cube = build_cube(name, d)
    shape = [len(v) for v in dom.values()]
    shape = tuple([len(metrics)] + shape)

    assert_dict_equal(cube.domain, dom)
    assert_dict_equal(cube.metadata, metadata)
    assert_equal(cube.metrics, metrics)
    assert_equal(len(params), len(cube.parameters))
    assert_equal(cube.shape, shape)
    for p in params:
        assert_in(p, cube.parameters)


def test_hasher():
    metrics = ["m1", "m2"]
    domain = {"v1":[0, 1, 2], "v2":[0, 1]}
    ls = []
    for m in metrics:
        for vv2 in domain["v2"]:
            for vv1 in domain["v1"]:
                ls.append((m, {"v1":vv1, "v2":vv2}))
    hasher = Hasher(metrics, domain)
    for index, (metric, params) in enumerate(ls):
        assert_equal(index, hasher.hash(metric, params))


def test_result_data():
    name, metadata, params, dom, metrics, d = basic()
    cube = build_cube(name, d)
    assert_equal(len(cube.data), len(d)*len(metrics))
    for x in cube.data:
        assert_not_equal(x, None)



# -*- coding: utf-8 -*-

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


from nose.tools import assert_dict_equal
from nose.tools import assert_equal
from nose.tools import assert_in


from clustertools import Result

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
    exp_name = "basic"
    return exp_name, metadata, parameters, domain, res

def build_cube(exp_name, res):
    parameterss = []
    resultss = []
    for d in res.values():
        parameterss.append(d["Parameters"])
        resultss.append(d["Results"])
    return Result(parameterss, resultss, exp_name)


def test_info():
    name, metadata, params, dom, d = basic()
    cube = build_cube(name, d)
    assert_dict_equal(cube.domain, dom)
    assert_dict_equal(cube.metadata, metadata)
    assert_equal(len(params), len(cube.parameters))
    for p in params:
        assert_in(p, cube.parameters)









# -*- coding: utf-8 -*-

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


from nose.tools import assert_dict_equal
from nose.tools import assert_equal
from nose.tools import assert_not_equal
from nose.tools import assert_in
from nose.tools import assert_raises
from nose.tools import assert_true


from clustertools import Result, Hasher

def basic():
    """
    values
           w              w
         5   6          5    6
       +---+---+      +---+----+
      1| 2 | 2 |     1| 9 | 10 |
       +---+---+      +---+----+
    x 2| 4 | 4 |   x 2| 9 | 10 |
       +---+---+      +---+----+
      3| 6 | 6 |     3| 9 | 10 |
       +---+---+      +---+----+
           f1             f2
    /!\ tranposed
    """
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
    domain = {'x':["1", "2", "3"], 'w':["5", "6"]}
    metadata = {'z':"4"}
    parameters = ["x", "w"]
    parameters.sort()
    metrics = ["f1", "f2"]
    metrics.sort()
    exp_name = "basic"
    return exp_name, metadata, parameters, domain, metrics, res


def alldiff():
    """
    values
            w                w
          5    6           5    6
       +----+----+      +----+----+
      1| 15 | 16 |     1| 51 | 61 |
       +----+----+      +----+----+
    x 2| 24 | 26 |   x 2| 52 | 62 |
       +----+----+      +----+----+
      3| 35 | 36 |     3| 53 | 63 |
       +----+----+      +----+----+
           f1             f2
    /!\ tranposed
    """
    res = {u'Computation-alldiff-0': {'Experiment': 'alldiff',
            'Parameters': {u'w': 5, u'x': 1, u'z': 4},
            'Results': {'f1': 15, 'f2': 51}},
            u'Computation-alldiff-1': {'Experiment': 'alldiff',
            'Parameters': {u'w': 6, u'x': 1, u'z': 4},
            'Results': {'f1': 16, 'f2': 61}},
            u'Computation-alldiff-2': {'Experiment': 'alldiff',
            'Parameters': {u'w': 5, u'x': 2, u'z': 4},
            'Results': {'f1': 25, 'f2': 52}},
            u'Computation-alldiff-3': {'Experiment': 'alldiff',
            'Parameters': {u'w': 6, u'x': 2, u'z': 4},
            'Results': {'f1': 26, 'f2': 62}},
            u'Computation-alldiff-4': {'Experiment': 'alldiff',
            'Parameters': {u'w': 5, u'x': 3, u'z': 4},
            'Results': {'f1': 35, 'f2': 53}},
            u'Computation-alldiff-5': {'Experiment': 'alldiff',
            'Parameters': {u'w': 6, u'x': 3, u'z': 4},
            'Results': {'f1': 36, 'f2': 63}}}

    # Notice the ordering
    domain = {'x':["1", "2", "3"], 'w':["5", "6"]}
    metadata = {'z':"4"}
    parameters = ["x", "w"]
    parameters.sort()
    metrics = ["f1", "f2"]
    metrics.sort()
    exp_name = "alldiff"
    return exp_name, metadata, parameters, domain, metrics, res


def some_ood():
    """
    values
            w                w
          5    6           5    6
       +----+----+      +----+----+
      1| 15 | 16 |     1| 51 | 61 |
       +----+----+      +----+----+
    x 2| N/ | 26 |   x 2| N/ | 62 |
       +----+----+      +----+----+
      3| 35 | 36 |     3| 53 | 63 |
       +----+----+      +----+----+
           f1             f2
    /!\ tranposed
    """
    res = {u'Computation-alldiff-0': {'Experiment': 'alldiff',
            'Parameters': {u'w': 5, u'x': 1, u'z': 4},
            'Results': {'f1': 15, 'f2': 51}},
            u'Computation-alldiff-1': {'Experiment': 'alldiff',
            'Parameters': {u'w': 6, u'x': 1, u'z': 4},
            'Results': {'f1': 16, 'f2': 61}},
            u'Computation-alldiff-2': {'Experiment': 'alldiff',
            'Parameters': {u'w': 5, u'x': 2, u'z': 4},
            'Results': {'f1': None, 'f2': None}},
            u'Computation-alldiff-3': {'Experiment': 'alldiff',
            'Parameters': {u'w': 6, u'x': 2, u'z': 4},
            'Results': {'f1': 26, 'f2': 62}},
            u'Computation-alldiff-4': {'Experiment': 'alldiff',
            'Parameters': {u'w': 5, u'x': 3, u'z': 4},
            'Results': {'f1': 35, 'f2': 53}},
            u'Computation-alldiff-5': {'Experiment': 'alldiff',
            'Parameters': {u'w': 6, u'x': 3, u'z': 4},
            'Results': {'f1': 36, 'f2': 63}}}

    # Notice the ordering
    domain = {'x':["1", "2", "3"], 'w':["5", "6"]}
    metadata = {'z':"4"}
    parameters = ["x", "w"]
    parameters.sort()
    metrics = ["f1", "f2"]
    metrics.sort()
    exp_name = "alldiff"
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

    assert_dict_equal(cube.domain, dom)
    assert_dict_equal(cube.metadata, metadata)
    assert_equal(cube.metrics, metrics)
    assert_equal(len(params), len(cube.parameters))
    assert_equal(cube.shape, (2, 3, 2))#w/x/m
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

def test_call():
    name, metadata, params, dom, metrics, d = basic()
    cube = build_cube(name, d)
    assert_equal(id(cube), id(cube()))

def test_indexing():
    name, metadata, params, dom, metrics, d = alldiff()
    cube = build_cube(name, d)
    # f1(w=5, x=1)
    assert_equal(cube[0, 0, 0], 15)
    # f1(w=6, x=1)
    assert_equal(cube[1, 0, 0], 16)
    # f1(w=5, x=2)
    assert_equal(cube[0, 1, 0], 25)
    # f1(w=6, x=2)
    assert_equal(cube[1, 1, 0], 26)
    # f1(w=5, x=3)
    assert_equal(cube[0, 2, 0], 35)
    # f1(w=6, x=3)
    assert_equal(cube[1, 2, 0], 36)
    # f2(w=5, x=1)
    assert_equal(cube[0, 0, 1], 51)
    # f2(w=6, x=1)
    assert_equal(cube[1, 0, 1], 61)
    # f2(w=5, x=2)
    assert_equal(cube[0, 1, 1], 52)
    # f2(w=6, x=2)
    assert_equal(cube[1, 1, 1], 62)
    # f2(w=5, x=3)
    assert_equal(cube[0, 2, 1], 53)
    # f2(w=6, x=3)
    assert_equal(cube[1, 2, 1], 63)

    assert_raises(IndexError, cube.__getitem__, (1, 2, 3, 4, 5))


def test_call_indexing():
    name, metadata, params, dom, metrics, d = alldiff()
    cube = build_cube(name, d)
    # f1(w=5, x=1)
    assert_equal(cube(w=0, x=0, metric=0), 15)
    # f1(w=6, x=1)
    assert_equal(cube(w=1, x=0, metric=0), 16)
    # f1(w=5, x=2)
    assert_equal(cube(metric=0, w=0, x=1), 25)
    # f1(w=6, x=2)
    assert_equal(cube(0, w=1, x=1), 26)
    # f1(w=5, x=3)
    assert_equal(cube(w=0, x=2, metric="f1"), 35)
    # f1(w=6, x=3)
    assert_equal(cube("f1", w=1, x=2), 36)
    # f2(w=5, x=1)
    assert_equal(cube(w=0, x=0, metric=1), 51)
    # f2(w=6, x=1)
    assert_equal(cube(1, w=1, x=0), 61)
    # f2(w=5, x=2)
    assert_equal(cube(metric=1, w=0, x=1), 52)
    # f2(w=6, x=2)
    assert_equal(cube(w=1, x=1, metric="f2"), 62)
    # f2(w=5, x=3)
    assert_equal(cube(w=0, x=2, metric=1), 53)
    # f2(w=6, x=3)
    assert_equal(cube("f2", w=1, x=2), 63)

    assert_raises(KeyError, cube, "f3")




def test_indexing_name():
    name, metadata, params, dom, metrics, d = alldiff()
    cube = build_cube(name, d)
    print cube.parameters
    # f1(w=5, x=1)
    assert_equal(cube["5", "1", "f1"], 15)
    # f1(w=6, x=1)
    assert_equal(cube["6", 0, 0], 16)
    # f1(w=5, x=2)
    assert_equal(cube[0, "2", 0], 25)
    # f1(w=6, x=2)
    assert_equal(cube[1, 1, "f1"], 26)
    # f2(w=5, x=1)
    assert_equal(cube["5", "1", "f2"], 51)
    # f2(w=6, x=1)
    assert_equal(cube["6", 0, 1], 61)
    # f2(w=5, x=2)
    assert_equal(cube[0, "2", 1], 52)
    # f2(w=6, x=2)
    assert_equal(cube[1, 1, "f2"], 62)


def test_call_indexing_name():
    name, metadata, params, dom, metrics, d = alldiff()
    cube = build_cube(name, d)
    # f1(w=5, x=1)
    assert_equal(cube(w="5", x="1", metric="f1"), 15)
    # f1(w=6, x=1)
    assert_equal(cube(w="6", x=0, metric=0), 16)
    # f2(w=5, x=2)
    assert_equal(cube(metric="f2", w=0, x="2"), 52)




def test_slicing():
    name, metadata, params, dom, metrics, d = alldiff()
    cube = build_cube(name, d)
    # ==== False slicing ====
    cube2 = cube[...]
    assert_equal(id(cube2), id(cube))
    cube2 = cube[:, :, :]
    assert_equal(id(cube2), id(cube))
    cube2 = cube[:, ...]
    assert_equal(id(cube2), id(cube))
    cube2 = cube[..., :, ...]
    assert_equal(id(cube2), id(cube))
    cube2 = cube[:]
    assert_equal(id(cube2), id(cube))
    try:
        cube2 = cube[0, 0]
    except TypeError:
        # TODO nicefy
        assert_true(False)

    # ==== Partial slicing: removing a dim ====
    # x=1
    cube2 = cube[:, 0, ...]
    assert_not_equal(id(cube2), id(cube))
    assert_dict_equal(cube2.domain, {"w":["5", "6"]})
    assert_dict_equal(cube2.metadata, {"z":"4", "x":"1"})
    assert_equal(cube2.parameters, ["w"])
    assert_equal(cube2.metrics, cube.metrics)
    assert_equal(cube2.size(), 4)
    assert_equal(cube2.shape, (2, 2))# w/m

    # ==== Partial slicing: not removing a dim ====
     # x \in {1, 2}
    cube2 = cube[:, 0:2]
    assert_not_equal(id(cube2), id(cube))
    assert_dict_equal(cube2.domain, {"x":["1","2"], "w":["5", "6"]})
    assert_dict_equal(cube2.metadata, cube.metadata)
    assert_equal(cube2.parameters, cube.parameters)
    assert_equal(cube2.metrics, cube.metrics)
    assert_equal(cube2.size(), 8)
    assert_equal(cube2.shape, (2, 2, 2))#w/x/m

    # ==== Partial slicing: not removing a dim ====
     # x \in {1, 3}
    cube2 = cube[:, [0, 2]]
    assert_not_equal(id(cube2), id(cube))
    assert_dict_equal(cube2.domain, {"x":["1","3"], "w":["5", "6"]})
    assert_dict_equal(cube2.metadata, cube.metadata)
    assert_equal(cube2.parameters, cube.parameters)
    assert_equal(cube2.metrics, cube.metrics)
    assert_equal(cube2.size(), 8)
    assert_equal(cube2.shape, (2, 2, 2))#w/x/m


    # ==== Partial slicing: selecting a metric ====
    # metrics = f1
    cube2 = cube[..., 0]
    assert_not_equal(id(cube2), id(cube))
    assert_dict_equal(cube2.domain, {"x":["1","2", "3"], "w":["5", "6"]})
    assert_dict_equal(cube2.metadata, cube.metadata)
    assert_equal(cube2.parameters, cube.parameters)
    assert_equal(cube2.metrics, ["f1"])
    assert_equal(cube2.size(), 6)
    assert_equal(cube2.shape, (2, 3, 1))#w/x/m

    # ==== Swapping the metrics ====
    cube2 = cube[:, :, ["f2", 0]]
    assert_equal(cube2.metrics, ["f2", "f1"])



def test_numpify():
    import numpy as np
    # TODO skip if not numpy
    name, metadata, params, dom, metrics, d = alldiff()
    cube = build_cube(name, d)
    cube2 = cube[0, 0]
    assert_equal(len(cube2.parameters), 0)
    numpified = cube2.numpify()
    assert_equal(numpified.shape, (2, ))
    for v1, v2 in zip(numpified, [15, 51]):
        assert_equal(v1, v2)
    arr1 = np.array([[15, 25, 35], [16, 26, 36]])
    arr2 = np.array([[51, 52, 53], [61, 62, 63]])
    array = np.dstack([arr1, arr2])
    numpified = cube.numpify()
    assert_equal(numpified.shape, array.shape)
    for v1, v2 in zip(numpified, array):
        for v11, v22 in zip(v1, v2):
            for v111, v222 in zip(v11, v22):
                assert_equal(v111, v222)


def test_reorder():
    name, metadata, params, dom, metrics, d = alldiff()
    cube = build_cube(name, d)
    p2 = ["x", "w"]
    cube.reorder_parameters(*p2)
    assert_equal(cube.parameters, p2)
    cube.reorder_parameters("w")
    assert_equal(cube.parameters, params)


def test_iteritems():
    name, metadata, params, dom, metrics, d = alldiff()
    cube = build_cube(name, d)
    ls = [( ("5", "1"), (15, 51) ),
          ( ("5", "2"), (25, 52) ),
          ( ("5", "3"), (35, 53) ),
          ( ("6", "1"), (16, 61) ),
          ( ("6", "2"), (26, 62) ),
          ( ("6", "3"), (36, 63) )]
    ls.sort()
    rs = list(cube.iteritems())
    rs.sort()
    assert_equal(ls, rs)

def test_ood():
    name, metadata, params, dom, metrics, d = some_ood()
    cube = build_cube(name, d)
    expected_ood = [( {"x":"2", "w":"5"}, "f1"),
                    ( {"x":"2", "w":"5"}, "f2")]
    ood = cube.out_of_domain()
    assert_equal(len(ood), len(expected_ood))
    assert_dict_equal(expected_ood[0][0], ood[0][0])
    assert_dict_equal(expected_ood[1][0], ood[1][0])
    exp_m = [x for _, x in expected_ood]
    m = [x for _, x in ood]
    exp_m.sort()
    m.sort()
    assert_equal(m, exp_m)

# def test_max_hypercube():
#     name, metadata, params, dom, metrics, d = some_ood()
#     cube = build_cube(name, d)
#     cube2 = cube.maximal_hypercube()
#     # print cube2.parameters
#     # print cube2.domain
#     # print cube2.metrics
#     # print cube2.metadata
#     assert_equal(cube2.shape, (2, 2, 2))#w/x/m


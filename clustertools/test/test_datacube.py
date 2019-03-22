# -*- coding: utf-8 -*-
from unittest import SkipTest

from nose.tools import assert_dict_equal, assert_not_in, assert_equal, \
    assert_not_equal, assert_in, assert_true, assert_raises

from clustertools.datacube import Datacube, Hasher, build_datacube

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


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
    res = {'Computation-basic-0': {'Experiment': 'basic',
            'Parameters': {'w': 5, 'x': 1, 'z': 4},
            'Results': {'f1': 2, 'f2': 9}},
            'Computation-basic-1': {'Experiment': 'basic',
            'Parameters': {'w': 6, 'x': 1, 'z': 4},
            'Results': {'f1': 2, 'f2': 10}},
            'Computation-basic-2': {'Experiment': 'basic',
            'Parameters': {'w': 5, 'x': 2, 'z': 4},
            'Results': {'f1': 4, 'f2': 9}},
            'Computation-basic-3': {'Experiment': 'basic',
            'Parameters': {'w': 6, 'x': 2, 'z': 4},
            'Results': {'f1': 4, 'f2': 10}},
            'Computation-basic-4': {'Experiment': 'basic',
            'Parameters': {'w': 5, 'x': 3, 'z': 4},
            'Results': {'f1': 6, 'f2': 9}},
            'Computation-basic-5': {'Experiment': 'basic',
            'Parameters': {'w': 6, 'x': 3, 'z': 4},
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
    x 2| 25 | 26 |   x 2| 52 | 62 |
       +----+----+      +----+----+
      3| 35 | 36 |     3| 53 | 63 |
       +----+----+      +----+----+
           f1             f2
    /!\ tranposed
    """
    res = {'Computation-alldiff-0': {'Experiment': 'alldiff',
            'Parameters': {'w': 5, 'x': 1, 'z': 4},
            'Results': {'f1': 15, 'f2': 51}},
            'Computation-alldiff-1': {'Experiment': 'alldiff',
            'Parameters': {'w': 6, 'x': 1, 'z': 4},
            'Results': {'f1': 16, 'f2': 61}},
            'Computation-alldiff-2': {'Experiment': 'alldiff',
            'Parameters': {'w': 5, 'x': 2, 'z': 4},
            'Results': {'f1': 25, 'f2': 52}},
            'Computation-alldiff-3': {'Experiment': 'alldiff',
            'Parameters': {'w': 6, 'x': 2, 'z': 4},
            'Results': {'f1': 26, 'f2': 62}},
            'Computation-alldiff-4': {'Experiment': 'alldiff',
            'Parameters': {'w': 5, 'x': 3, 'z': 4},
            'Results': {'f1': 35, 'f2': 53}},
            'Computation-alldiff-5': {'Experiment': 'alldiff',
            'Parameters': {'w': 6, 'x': 3, 'z': 4},
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
    x 2|    | 26 |   x 2|    | 62 |
       +----+----+      +----+----+
      3| 35 | 36 |     3| 53 | 63 |
       +----+----+      +----+----+
           f1             f2
    /!\ tranposed
    """
    res = {'Computation-alldiff-0': {'Experiment': 'alldiff',
            'Parameters': {'w': 5, 'x': 1, 'z': 4},
            'Results': {'f1': 15, 'f2': 51}},
            'Computation-alldiff-1': {'Experiment': 'alldiff',
            'Parameters': {'w': 6, 'x': 1, 'z': 4},
            'Results': {'f1': 16, 'f2': 61}},
            'Computation-alldiff-2': {'Experiment': 'alldiff',
            'Parameters': {'w': 5, 'x': 2, 'z': 4},
            'Results': {'f1': None, 'f2': None}},
            'Computation-alldiff-3': {'Experiment': 'alldiff',
            'Parameters': {'w': 6, 'x': 2, 'z': 4},
            'Results': {'f1': 26, 'f2': 62}},
            'Computation-alldiff-4': {'Experiment': 'alldiff',
            'Parameters': {'w': 5, 'x': 3, 'z': 4},
            'Results': {'f1': 35, 'f2': 53}},
            'Computation-alldiff-5': {'Experiment': 'alldiff',
            'Parameters': {'w': 6, 'x': 3, 'z': 4},
            'Results': {'f1': 36, 'f2': 63}}}

    # Notice the ordering
    domain = {'x':["1", "2", "3"], 'w':["5", "6"]}
    metadata = {'z':"4"}
    parameters = ["x", "w"]
    parameters.sort()
    metrics = ["f1", "f2"]
    metrics.sort()
    exp_name = "some_ood"
    return exp_name, metadata, parameters, domain, metrics, res


def some_meta():
    """
    values
            w                w
          5    6           5    6
       +----+----+      +----+----+
      1| 15 | 16 |     1| 51 | 61 |
       +----+----+      +----+----+
    x 2| 25 | 26 |   x 2| 52 | 62 |
       +----+----+      +----+----+
      3| 35 | 36 |     3| 53 | 63 |
       +----+----+      +----+----+
           f1             f2
    /!\ tranposed
    """
    res = {'Computation-somemeta-0': {'Experiment': 'somemeta',
            'Parameters': {'w': 5, 'x': 1, 'z': 4, 'y':7},
            'Results': {'f1': 15, 'f2': 51}},
            'Computation-somemeta-1': {'Experiment': 'somemeta',
            'Parameters': {'w': 6, 'x': 1, 'z': 4, 'y':7},
            'Results': {'f1': 16, 'f2': 61}},
            'Computation-somemeta-2': {'Experiment': 'somemeta',
            'Parameters': {'w': 5, 'x': 2, 'z': 4, 'y':7},
            'Results': {'f1': 25, 'f2': 52}},
            'Computation-somemeta-3': {'Experiment': 'somemeta',
            'Parameters': {'w': 6, 'x': 2, 'z': 4, 'y':7},
            'Results': {'f1': 26, 'f2': 62}},
            'Computation-somemeta-4': {'Experiment': 'somemeta',
            'Parameters': {'w': 5, 'x': 3, 'z': 4, 'y':7},
            'Results': {'f1': 35, 'f2': 53}},
            'Computation-somemeta-5': {'Experiment': 'somemeta',
            'Parameters': {'w': 6, 'x': 3, 'z': 4, 'y':7},
            'Results': {'f1': 36, 'f2': 63}}}

    # Notice the ordering
    domain = {'x':["1", "2", "3"], 'w':["5", "6"]}
    metadata = {'z':"4", 'y':'7'}
    parameters = ["x", "w"]
    parameters.sort()
    metrics = ["f1", "f2"]
    metrics.sort()
    exp_name = "somemeta"
    return exp_name, metadata, parameters, domain, metrics, res


def build_cube(exp_name, res, autopacking=False):
    parameterss = []
    resultss = []
    for d in res.values():
        parameterss.append(d["Parameters"])
        resultss.append(d["Results"])
    return Datacube(parameterss, resultss, exp_name, autopacking=autopacking)


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
    domain = {"v1": [0, 1, 2], "v2": [0, 1]}
    ls = []
    for m in metrics:
        for vv2 in domain["v2"]:
            for vv1 in domain["v1"]:
                ls.append((m, {"v1": vv1, "v2": vv2}))
    hasher = Hasher(metrics, domain)
    seen = set()
    for metric, params in ls:
        index = hasher.hash(metric, params)
        assert_not_in(index, seen)
        seen.add(index)
    assert_equal(0, min(seen))
    assert_equal(len(ls)-1, max(seen))


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


def test_indexing_path():
    name, metadata, params, dom, metrics, d = alldiff()
    cube = build_cube(name, d)
    val = cube(w="5", x="2", metric="f1")
    c2 = cube(w="5", x="2")
    val2 = c2(metric="f1")
    vs = [v for v in c2]
    assert_equal(vs[c2.metrics.index("f1")], val)
    assert_equal(val, val2)


def test_numpyfy():
    try:
        import numpy as np
    except ImportError:
        raise SkipTest("numpy is not installed")
    name, metadata, params, dom, metrics, d = alldiff()
    cube = build_cube(name, d)
    cube2 = cube[0, 0]
    assert_equal(len(cube2.parameters), 0)
    numpified = cube2.numpyfy(False)
    assert_equal(numpified.shape, (2, ))
    for v1, v2 in zip(numpified, [15, 51]):
        assert_equal(v1, v2)
    arr1 = np.array([[15, 25, 35], [16, 26, 36]])
    arr2 = np.array([[51, 52, 53], [61, 62, 63]])
    array = np.dstack([arr1, arr2])
    numpified = cube.numpyfy(False)
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


def test_items():
    name, metadata, params, dom, metrics, d = alldiff()
    cube = build_cube(name, d)
    ls = [( ("5", "1"), (15, 51) ),
          ( ("5", "2"), (25, 52) ),
          ( ("5", "3"), (35, 53) ),
          ( ("6", "1"), (16, 61) ),
          ( ("6", "2"), (26, 62) ),
          ( ("6", "3"), (36, 63) )]
    ls.sort()
    rs = list(cube.items())
    rs.sort()
    assert_equal(ls, rs)


def test_ood():
    name, metadata, params, dom, metrics, d = some_ood()
    cube = build_cube(name, d)
    expected_ood = [({"x": "2", "w": "5"}, "f1"),
                    ({"x": "2", "w": "5"}, "f2")]
    ood = cube.out_of_domain()
    assert_equal(len(ood), len(expected_ood))
    assert_dict_equal(expected_ood[0][0], ood[0][0])
    assert_dict_equal(expected_ood[1][0], ood[1][0])
    exp_m = [x for _, x in expected_ood]
    m = [x for _, x in ood]
    exp_m.sort()
    m.sort()
    assert_equal(m, exp_m)


def test_ood_nan():
    # missing values should be marked as nan
    try:
        import numpy as np
    except ImportError:
        raise SkipTest("numpy is not installed")
    name, metadata, params, dom, metrics, d = some_ood()
    cube = build_cube(name, d)
    arr = cube.numpyfy(True)
    assert_true(np.issubdtype(arr.dtype, np.float))
    try:
        assert_true(np.isnan(arr).any())
    except:
        assert_true(False, "Exception was raised, nan is not working")


def test_ood_iter_dimensions():
    name, metadata, params, dom, metrics, d = some_ood()
    cube = build_cube(name, d)
    for (x, w), cube_i in cube.iter_dimensions("x", "w"):
        x = int(x)
        w = int(w)
        v = cube_i("f1")
        if x == 2 and w == 5:
            assert_true(v is None)
        else:
            assert_true(v is not None)


# def test_max_hypercube():
#     name, metadata, params, dom, metrics, d = some_ood()
#     cube = build_cube(name, d)
#     cube2 = cube.maximal_hypercube()
#     # print cube2.parameters
#     # print cube2.domain
#     # print cube2.metrics
#     # print cube2.metadata
#     assert_equal(cube2.shape, (2, 2, 2))#w/x/m


def test_iter_dimensions():
    name, metadata, params, dom, metrics, d = some_meta()
    cube = build_cube(name, d)
    """
    values
            w                w
          5    6           5    6
       +----+----+      +----+----+
      1| 15 | 16 |     1| 51 | 61 |
       +----+----+      +----+----+
    x 2| 25 | 26 |   x 2| 52 | 62 |
       +----+----+      +----+----+
      3| 35 | 36 |     3| 53 | 63 |
       +----+----+      +----+----+
           f1             f2
    /!\ tranposed
    """
    # y=7, z=4 are metadata
    expected = [
        (('1', '7', '5', '4'), 15),
        (('1', '7', '6', '4'), 16),
        (('2', '7', '5', '4'), 25),
        (('2', '7', '6', '4'), 26),
        (('3', '7', '5', '4'), 35),
        (('3', '7', '6', '4'), 36),
    ]
    for (values, cube_i), (exp_val, exp_res) in zip(cube.iter_dimensions("x", "y", "w", "z"), expected):
        assert_equal(values, exp_val)
        assert_equal(cube_i("f1"), exp_res)


def test_truly_empty_cube():
    # Force = False
    assert_raises(ValueError, build_datacube,
                  "This_is_a_mock_exp2423R43RFDSBNET", force=False)

    # Force true
    try:
        cube = build_datacube("This_is_a_mock_exp2423R43RFDSBNET", force=True)
        assert_true(True, "Datacube creation circumvent empty parameters when "
                          "force=True")
    except ValueError:
        assert_true(False, "Datacube creation did not circumvent empty "
                           "parameters when force=True")

    assert_raises(AttributeError, cube.diagnose)


def test_dicing_in_metadata():
    name, metadata, params, dom, metrics, d = alldiff()
    cube = build_cube(name, d)
    try:
        assert_equal(cube("f1", x="1", w="5", z="4"), 15)
    except IndexError:
        assert_true(False, "Raised IndexError")


def test_packing():
    name, metadata, params, dom, metrics, d = some_ood()
    cube = build_cube(name, d)(w="5").minimal_hypercube()  # x=2 disappears
    assert_equal(cube.size(), 4)  # (x=1 and x=3) (f1 and f2)
    assert_equal(cube.diagnose()["Missing ratio"], 0)


def test_autopacking():
    name, metadata, params, dom, metrics, d = some_ood()
    cube = build_cube(name, d, autopacking=True)(w="5")  # x=2 disappears
    assert_equal(cube.size(), 4)  # (x=1 and x=3) (f1 and f2)
    assert_equal(cube.diagnose()["Missing ratio"], 0)

    # Test for scalar
    cube2 = cube(x="1")
    assert_equal(cube2("f1"), 15)


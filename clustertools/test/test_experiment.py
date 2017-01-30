# -*- coding: utf-8 -*-

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


from nose.tools import assert_equal
from nose.tools import assert_raises


from clustertools import Experiment


def test_len():
    exp = Experiment("TestLen")

    exp.add_params(p1=1, p2=[2, 3], p3="param")
    exp.add_params(p1=4, p2=5)

    assert_equal(len(exp), 6)
    i = 0
    for _ in exp:
        i += 1
    assert_equal(i, 6)
    assert_equal(len(exp), 6)


def test_getitem():
    exp = Experiment("TestItem")
    exp.add_params(p1=1, p2=[3, 2], p3="param")
    exp.add_params(p1=4, p2=5)


    assert_raises(KeyError, exp.get_params_for, -1)
    assert_raises(KeyError, exp.get_params_for, 10e6)

    labels = []
    params = []
    for l, p in exp:
        labels.append(l)
        params.append(p)

    for i, (l, p) in enumerate(zip(labels, params)):
        li, pi = exp[l]
        assert_equal(l, li)
        assert_equal(p, pi)

        li, pi = exp[i]
        assert_equal(l, li)
        assert_equal(p, pi)


def test_get_computation_with():
    exp = Experiment("TestGetComputationWith")
    exp.add_params(p1=[0, 1, 2])
    exp.add_params(p2=[10, 11, 12])
    exp.add_params(p3=[20,21])
    exp.add_separator()
    exp.add_params(p1=3)
    indices = [x for x,y in exp.get_computations_with(p1=3, p2=12)]
    expected = [22, 23]
    assert_equal(indices, expected)

    assert_equal(len(list(exp.get_computations_with(p1=-5))), 0)



# -*- coding: utf-8 -*-

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


from nose.tools import assert_in, assert_equal, assert_not_equal


from clustertools import ParameterSet
from clustertools.util import experiment_diff, reorder


def test_exp_diff():
    exp = ParameterSet("TestExpDiff")

    exp.add_params(p1=1, p2=[2, 3], p3="param")
    exp.add_params(p1=4, p2=5)

    labels = []
    params = []
    for l, p in exp:
        labels.append(l)
        params.append(p)
    for i in range(len(labels)):
        lab = labels[:i]
        par = params[:i]
        cmpts = {k:v for k,v in zip(lab, par)}
        res = experiment_diff(exp, cmpts)
        for l, p in res:
            assert_in(l, labels[i:])
            assert_in(p, params[i:])


def test_reorder():
    ls = range(10)
    indices = [2, 4, 1, 5]
    ls2 = reorder(ls, indices, in_place=True)
    assert_equal(ls2, ls[:len(indices)])
    assert_equal(len(ls2), len(indices))
    assert_equal(ls2, indices)

    ls = range(10)
    indices = [2, 4, 1, 5]
    ls2 = reorder(ls, indices, in_place=False)
    assert_not_equal(ls2, ls)
    assert_equal(len(ls2), len(indices))
    assert_equal(ls2, indices)

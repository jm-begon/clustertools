# -*- coding: utf-8 -*-

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


from nose.tools import assert_in


from clustertools import Experiment
from clustertools.util import experiment_diff


def test_exp_diff():
    exp = Experiment("TestExpDiff")

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



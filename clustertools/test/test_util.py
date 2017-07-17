# -*- coding: utf-8 -*-

from nose.tools import assert_equal, assert_not_equal

from clustertools.util import reorder

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


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

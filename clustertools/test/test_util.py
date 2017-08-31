# -*- coding: utf-8 -*-

from nose.tools import assert_equal, assert_not_equal

from clustertools.util import reorder, escape

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


def test_escape():
    s1 = "print 'hello'"
    expected1 = "print\\ \\'hello\\'"
    assert_equal(escape(s1), expected1)

    s2 = 'print "hello"'
    expected2 = 'print\\(\\"hello\\"\\)'
    assert_equal(escape(s2), expected2)

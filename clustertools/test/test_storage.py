# -*- coding: utf-8 -*-

from unittest import TestCase
from nose.tools import assert_in
from nose.tools import assert_equal
from nose.tools import with_setup

from clustertools.storage import PickleStorage

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


__EXP_NAME__ = "ClustertoolsTest"


def purge():
    storage = PickleStorage(__EXP_NAME__)
    try:
        storage.delete()
    except OSError:
        pass
    return storage


def prep():
    storage = purge()
    storage.init()


class TestAnchor(TestCase):
    pass


@with_setup(prep, purge)
def test_save_then_load_result():
    comp_name = "test_comp"
    parameters = {"a":1, "b":(2,3)}
    expected_result = {"r":10, "t":(11, 12)}
    storage = PickleStorage(__EXP_NAME__)
    storage.save_result(comp_name, parameters, expected_result)
    given_result = storage.load_result(comp_name)
    assert_equal(expected_result, given_result)





@with_setup(prep, purge)
def test_save_then_load_result_and_params():
    pass

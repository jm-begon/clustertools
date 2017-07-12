# -*- coding: utf-8 -*-

from nose.tools import assert_in
from nose.tools import assert_equal
from nose.tools import with_setup

from clustertools.storage import PickleStorage
from clustertools.state import PendingState, AbortedState, ManualInterruption

from .util_test import pickle_prep, pickle_purge, __EXP_NAME__

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


@with_setup(pickle_prep, pickle_purge)
def test_save_then_load_result():
    comp_name = "test_comp"
    parameters = {"a": 1, "b": (2,3)}
    expected_result = {"r": 10, "t": (11, 12)}
    storage = PickleStorage(__EXP_NAME__)
    storage.save_result(comp_name, parameters, expected_result)
    given_result = storage.load_result(comp_name)
    assert_equal(expected_result, given_result)


@with_setup(pickle_prep, pickle_purge)
def test_save_then_load_result_and_params():
    storage = PickleStorage(__EXP_NAME__)
    p1 = {"a": 1, "b": (2,3)}
    r1 = {"r": 10, "t": (11, 12)}
    p2 = {"a": 7}
    r2 ={"r": 70, "t": (110, 120)}
    storage.save_result("test_comp1", p1, r1)
    storage.save_result("test_comp2", p2, r2)
    # expectation
    default_meta = {"b": (20, 30)}
    p2.update(default_meta)
    p_expected, r_expected = storage.load_params_and_results(**default_meta)
    # check
    assert_equal(len(p_expected), 2)
    assert_in(p1, p_expected)
    assert_in(p2, p_expected)
    assert_equal(len(r_expected), 2)
    assert_in(r1, r_expected)
    assert_in(r2, r_expected)


@with_setup(pickle_prep, pickle_purge)
def test_save_then_load_state():
    storage = PickleStorage(__EXP_NAME__)
    pending = PendingState(__EXP_NAME__, "pending")
    abort_exp = ManualInterruption("Test")
    aborted = AbortedState(__EXP_NAME__, "aborted", abort_exp)
    # First storage
    storage.update_state(pending)
    storage.update_state(aborted)
    # Same after loading
    loaded = storage.load_states()
    assert_equal(len(loaded), 2)
    assert_in(pending, loaded)
    assert_in(aborted, loaded)
    # Update
    launchable = pending.reset()
    storage.update_state(launchable)
    # Test after second loading
    loaded = storage.load_states()
    assert_equal(len(loaded), 2)
    assert_in(launchable, loaded)
    assert_in(aborted, loaded)


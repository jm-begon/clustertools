# -*- coding: utf-8 -*-

from nose.tools import assert_equal, assert_in, assert_less, assert_raises, \
    with_setup, assert_true

from clustertools import ParameterSet, Result, Experiment
from clustertools.state import RunningState, CompletedState, AbortedState, \
    CriticalState, PartialState, LaunchableState
from clustertools.storage import PickleStorage

from .util_test import purge, prep, __EXP_NAME__, IntrospectStorage, \
    TestComputation, InterruptedComputation, pickle_prep, pickle_purge, \
    with_setup_

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


# ----------------------------------------------------------------------- Result

def test_result():
    expected = {"m"+str(x): x for x in range(1, 5)}
    result = Result("m1", m2=2, m3=6)
    result.m1 = 1
    result.m3 = 3
    result["m4"] = 4

    assert_equal(len(expected), len(result))
    for name, value in expected.items():
        assert_equal(result[name], value)
    for name, value in result.items():
        # redundant
        assert_equal(expected[name], value)
    dict(result)
    repr(result)


# ------------------------------------------------------------------ Computation

@with_setup(prep, purge)
def test_correct_computation():
    computation = TestComputation()
    intro_storage = computation.storage
    result1 = computation(x1=5, x2=2, x3=50)
    result2 = intro_storage.load_result(computation.comp_name)
    for result in result1, result2:
        assert_equal(len(result), 2)  # One real metric + repr
        assert_equal(result["mult"], 2 * 5)

    assert_equal(len(intro_storage.result_history), 1)  # Only one computation
    assert_equal(len(intro_storage.state_history), 1)  # Only one computation
    states = list(intro_storage.state_history.values())[0]
    # If correct, state should have followed the sequence:
    # Running (p=0), Running (p=1), Critical, Partial, Completed
    assert_equal(len(states), 5)
    assert_true(isinstance(states[0], RunningState))
    assert_true(isinstance(states[1], RunningState))
    assert_true(isinstance(states[2], CriticalState))
    assert_true(isinstance(states[3], PartialState))
    assert_true(isinstance(states[4], CompletedState))
    assert_equal(states[0].progress, 0.)
    assert_equal(states[1].progress, 1.)


@with_setup(prep, purge)
def test_error_computation():
    computation = TestComputation()
    intro_storage = computation.storage
    computation = computation.lazyfy(x1=5, x2=None, x3=50)
    assert_raises(TypeError, computation)  # 5*None
    assert_equal(len(intro_storage.result_history), 0)  # Computation not saved
    assert_equal(len(intro_storage.state_history), 1)  # Only one computation
    states = list(intro_storage.state_history.values())[0]
    # If correct (i.e. error occurs), state should have evolved as:
    # Running, Aborted
    assert_equal(len(states), 2)
    assert_true(isinstance(states[0], RunningState))
    assert_true(isinstance(states[1], AbortedState))


@with_setup(prep, purge)
def test_interrupted_computation():
    computation = InterruptedComputation()
    intro_storage = computation.storage
    assert_raises(KeyboardInterrupt, computation)
    assert_equal(len(intro_storage.result_history[computation.comp_name]), 0)
    state_history = intro_storage.state_history[computation.comp_name]
    # Running -> Launchable
    assert_equal(len(state_history), 2)
    assert_true(isinstance(state_history[0], RunningState))
    assert_true(isinstance(state_history[1], LaunchableState))


# ------------------------------------------------------------------- Experiment

@with_setup(prep, purge)
def test_experiment():
    parameter_set = ParameterSet()
    parameter_set.add_parameters(x1=range(3), x2=range(3))
    experiment = Experiment(__EXP_NAME__, parameter_set, TestComputation,
                            IntrospectStorage)
    assert_equal(len(list(experiment.yield_computations())), 9)
    # start=3 : skip 0,1,2
    assert_equal(len(list(experiment.yield_computations(start=3))), 6)
    # capacity=6 : skip 6, 7, 8
    assert_equal(len(list(experiment.yield_computations(capacity=6))), 6)


@with_setup_(pickle_prep, pickle_purge)
def do_auto_refresh(auto_refresh):

    parameter_set = ParameterSet()
    parameter_set.add_parameters(x1=range(3), x2=range(3))
    experiment = Experiment(__EXP_NAME__, parameter_set, TestComputation)

    # There should be 9 computations
    assert_equal(len(experiment), 9)
    count = 0
    for i, _ in enumerate(experiment.yield_computations(auto_refresh=auto_refresh)):
        if i == 0:
            state = CompletedState(
                Experiment.name_computation(experiment.exp_name, 6)
            )
            PickleStorage(experiment.exp_name).update_state(state)
        count += 1

    print("Auto refresh?", auto_refresh, "--", count)
    assert_equal(count, 8 if auto_refresh else 9)


def test_auto_refresh():
    do_auto_refresh(True)
    do_auto_refresh(False)




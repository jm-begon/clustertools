# -*- coding: utf-8 -*-

from nose.tools import assert_equal, assert_in, assert_less, assert_raises, \
    with_setup, assert_true

from clustertools import ParameterSet, ConstrainedParameterSet, Result, \
    Experiment, PrioritizedParamSet
from clustertools.state import RunningState, CompletedState, AbortedState, \
    CriticalState, PartialState, LaunchableState

from .util_test import purge, prep, __EXP_NAME__, IntrospectStorage, \
    TestComputation, InterruptedComputation

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


# ----------------------------------------------------------------- ParameterSet

def test_paramset_yield():
    ps = ParameterSet()

    assert_equal(len(ps), 1)  # The null dictionary

    ps.add_parameters(p1=1, p2=[2, 3], p3="param")
    ps.add_parameters(p1=4, p2=5)

    cart_prod = [
        {"p1": 1, "p2": 2, "p3": "param"},
        {"p1": 1, "p2": 3, "p3": "param"},
        {"p1": 1, "p2": 5, "p3": "param"},
        {"p1": 4, "p2": 2, "p3": "param"},
        {"p1": 4, "p2": 3, "p3": "param"},
        {"p1": 4, "p2": 5, "p3": "param"},
    ]

    assert_equal(len(ps), 6)
    i = 0
    for _, param_dict in ps:
        assert_in(param_dict, cart_prod)
        i += 1
    assert_equal(i, 6)
    assert_equal(len(ps), 6)


def test_paramset_list_insertion():
    ps = ParameterSet()
    ps.add_single_values(p1=(1, 2, 3), p2=(1, 2))
    assert_equal(len(ps), 1)
    for _, param_dict in ps:
        assert_equal(param_dict, {"p1": (1, 2, 3), "p2": (1, 2)})


def test_paramset_separator():
    ps = ParameterSet()
    ps.add_parameters(p1=[1, 2], p2=["a", "b"])
    ps.add_separator(p3="param")
    ps.add_parameters(p1=3)

    assert_equal(len(ps), 6)
    for i, param_dict in ps:
        assert_equal(param_dict["p3"], "param")
        if i < 4:
            assert_in(param_dict["p1"], [1, 2])
        else:
            assert_equal(param_dict["p1"], 3)

    ps.add_parameters(p2="c")
    assert_equal(len(ps), 9)
    count = 0
    for i, param_dict in ps:
        assert_equal(param_dict["p3"], "param")
        if i < 4:
            assert_in(param_dict["p1"], [1, 2])
            assert_in(param_dict["p2"], ["a", "b"])
        if param_dict["p1"] == 3 and param_dict["p2"] == "c":
            count += 1

    assert_equal(count, 1)

    assert_raises(ValueError, ps.add_parameters, p4=10)


def test_paramset_getitem():
    ps = ParameterSet()
    ps.add_parameters(p1=[1, 2], p2=["a", "b"])
    ps.add_separator(p3="param")
    ps.add_parameters(p1=3, p2="c")

    for i, param_dict in ps:
        assert_equal(param_dict, ps[i])


def test_paramset_get_indices_with():
    ps = ParameterSet()
    ps.add_parameters(p1=[1, 2], p2=["a", "b"])
    ps.add_separator(p3="param")
    ps.add_parameters(p1=3, p2="c")

    for index in ps.get_indices_with(p1={3}):
        assert_less(3, index)  # 0,1,2,3 --> [1,2] x [a,b]
        assert_equal(ps[index]["p1"], 3)

    assert_equal(len(list(ps.get_indices_with(p1={4}))), 0)


# ------------------------------------------------------ ConstrainedParameterSet

def test_constrainparamset():
    ps = ParameterSet()
    ps.add_parameters(p1=[1, 2, 3], p2=["a", "b"])

    cps = ConstrainedParameterSet(ps)
    cps.add_constraints(c1=lambda p1, p2: True if p2 == "a" else p1 % 2 == 0)

    assert_equal(len(cps), 4)  # (1, a), (2, a), (3, a), (2, b)

    expected = [{"p1": 1, "p2": "a"},
                {"p1": 2, "p2": "a"},
                {"p1": 3, "p2": "a"},
                {"p1": 2, "p2": "b"},
                ]
    for _, param_dict in cps:
        assert_in(param_dict, expected)


# ---------------------------------------------------------- PrioritizedParamSet
def test_prioritized_paramset():
    ps = ParameterSet()
    ps.add_parameters(p1=[1, 2, 3, 4], p2=["a", "b", "c"])

    pps = PrioritizedParamSet(ps)
    pps.prioritize("p2", "b")
    pps.prioritize("p1", 2)
    pps.prioritize("p1", 3)
    pps.prioritize("p2", "c")

    expected = [
        (4, {"p1": 2, "p2": "b"}),   # 12 = 0 2^0 + 0 2^1 + 1 2^2 + 1 2^ 3
        (7, {"p1": 3, "p2": "b"}),   # 10 = 0 2^0 + 1 2^1 + 0 2^2 + 1 2^ 3
        (1, {"p1": 1, "p2": "b"}),   # 8 = 0 2^0 + 0 2^1 + 0 2^2 + 1 2^ 3
        (10, {"p1": 4, "p2": "b"}),  # 8 = 0 2^0 + 0 2^1 + 0 2^2 + 1 2^ 3

        (5, {"p1": 2, "p2": "c"}),  # 5 = 1 2^0 + 0 2^1 + 1 2^2 + 0 2^ 3
        (3, {"p1": 2, "p2": "a"}),  # 4 = 0 2^0 + 0 2^1 + 1 2^2 + 0 2^ 3

        (8, {"p1": 3, "p2": "c"}),  # 3 = 1 2^0 + 1 2^1 + 0 2^2 + 0 2^ 3
        (6, {"p1": 3, "p2": "a"}),  # 2 = 0 2^0 + 2 2^1 + 0 2^2 + 0 2^ 3


        (2, {"p1": 1, "p2": "c"}),   # 1 = 1 2^0 + 0 2^1 + 0 2^2 + 0 2^ 3
        (11, {"p1": 4, "p2": "c"}),  # 1 = 1 2^0 + 0 2^1 + 0 2^2 + 0 2^ 3


        (0, {"p1": 1, "p2": "a"}),   # 0 = 0 2^0 + 0 2^1 + 0 2^2 + 0 2^ 3
        (9, {"p1": 4, "p2": "a"}),   # 0 = 0 2^0 + 0 2^1 + 0 2^2 + 0 2^ 3
    ]
    result = list(pps)
    assert_equal(result, expected)


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

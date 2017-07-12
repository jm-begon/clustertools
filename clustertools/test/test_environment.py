# -*- coding: utf-8 -*-

from functools import partial

from nose.tools import assert_equal, assert_in, assert_less, assert_raises, \
    with_setup, assert_true

from clustertools import ParameterSet, ConstrainedParameterSet, Result, \
    Computation, PartialComputation, Experiment
from clustertools.environment import Session, InSituEnvironment, \
    BashEnvironment, ClusterlibEnvironment

from clusterlib._testing import skip_if_no_backend

from .util_test import purge, prep, __EXP_NAME__, IntrospectStorage, \
    TestComputation

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


# ------------------------------------------------------------------- Session
# Assumes InSituEnvironment works correctly
def test_session():
    parameter_set = ParameterSet()
    parameter_set.add_parameters(x1=range(3), x2=range(3))
    experiment = Experiment(__EXP_NAME__, parameter_set, TestComputation,
                            IntrospectStorage)

    env = InSituEnvironment(fail_fast=True)
    session = Session(env)
    assert_raises(ValueError, partial(session.run, TestComputation()))
    with session:
        for lazy_computation in experiment.yield_computations():
            session.run(lazy_computation)
    assert_equal(session.n_launch, 9)

    assert_raises(ValueError, partial(session.run, TestComputation()))


# ------------------------------------------------------------------ Environment
def enviornement_testing(environment):
    print(repr(environment))
    pass


def test_bash_environment():
    environment = BashEnvironment()
    enviornement_testing(environment)


@skip_if_no_backend
def test_clusterlib_environment():
    environment = ClusterlibEnvironment(time="0:20:00", memory="1000")
    enviornement_testing(environment)








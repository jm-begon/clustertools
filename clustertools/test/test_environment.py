# -*- coding: utf-8 -*-

from functools import partial

from nose.tools import assert_equal, assert_in, assert_less, assert_raises, \
    with_setup, assert_true, assert_false

from clustertools import ParameterSet, Experiment
from clustertools.environment import InSituEnvironment, \
    BashEnvironment, ClusterlibEnvironment, Serializer, FileSerializer
from clustertools.storage import PickleStorage

from clusterlib._testing import skip_if_no_backend

from .util_test import purge, prep, pickle_prep, pickle_purge, \
    __EXP_NAME__, IntrospectStorage, TestComputation

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


# ---------------------------------------------------------------------- Session
# Assumes InSituEnvironment works correctly

@with_setup(prep, purge)
def test_session():
    parameter_set = ParameterSet()
    parameter_set.add_parameters(x1=range(3), x2=range(3))
    experiment = Experiment(__EXP_NAME__, parameter_set, TestComputation,
                            IntrospectStorage)

    env = InSituEnvironment(fail_fast=True)
    session = env.create_session(experiment)
    assert_false(session.is_open())
    assert_raises(ValueError, partial(session.run, TestComputation()))
    with session:
        for lazy_computation in experiment.yield_computations():
            session.run(lazy_computation)
        assert_equal(session.n_launch, 9)

    assert_false(session.is_open())
    assert_raises(ValueError, partial(session.run, TestComputation()))


# ---------------------------------------------- Environment: integrated testing
# TODO how to test the logging is working correctly ?

@with_setup(pickle_prep, pickle_purge)
def environment_integration(environment):
    print(repr(environment))  # In case of error, prints the type of environment
    parameter_set = ParameterSet()
    parameter_set.add_parameters(x1=range(3), x2=range(3))
    experiment = Experiment(__EXP_NAME__, parameter_set,
                            TestComputation,
                            PickleStorage)
    environment.run(experiment, start=2, capacity=5)
    storage = experiment.storage
    parameters_ls, result_ls = storage.load_params_and_results()

    assert_equal(len(parameters_ls), 5)   # 5 computations
    assert_equal(len(result_ls), 5)  # 5 computations
    for parameters, result in zip(parameters_ls, result_ls):
        assert_equal(parameters["x1"]*parameters["x2"], result["mult"])


def test_bash_environment():
    for serializer in  FileSerializer(), Serializer():
        environment = BashEnvironment(serializer)
        environment_integration(environment)


@skip_if_no_backend
def test_clusterlib_environment():
    environment = ClusterlibEnvironment(time="0:20:00", memory="1000")
    environment_integration(environment)
    # TODO how to test the code is run by slurm/sge ?


# ------------------------------------------------------------------- Serializer
@with_setup(prep, purge)
def serializer_evaluation(serializer):
    print(repr(serializer))
    computation = TestComputation().lazyfy(x1=5, x2=10)
    computation = serializer.deserialize(serializer.serialize(computation))
    result = computation()
    assert_equal(len(result), 1)  # only one metric
    assert_equal(result.mult, 5*10)  #  correct result


def test_serializer():
    serializer_evaluation(Serializer())


def test_file_serializer():
    serializer_evaluation(FileSerializer())
# -*- coding: utf-8 -*-
import shutil
from functools import partial

from nose.tools import assert_equal, assert_in, assert_less, assert_raises, \
    with_setup, assert_true, assert_false
from nose.tools import assert_is_instance
from nose.tools import assert_is_none

from clustertools import ParameterSet, Experiment
from clustertools.environment import InSituEnvironment, \
    BashEnvironment, SlurmEnvironment, Serializer, FileSerializer, \
    DebugEnvironment
from clustertools.storage import PickleStorage

from .util_test import purge, prep, pickle_prep, pickle_purge, \
    __EXP_NAME__, IntrospectStorage, TestComputation, with_setup_, \
    skip_if_usuable

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


# ----------------------------------------------------- Environment class method
def test_usability():
    assert_equal(InSituEnvironment.is_usable(), True)
    assert_equal(BashEnvironment.is_usable(), True)
    assert_equal(SlurmEnvironment.is_usable(),
                 shutil.which("scontrol") is not None)


def test_list_up_jobs():
    assert_is_none(InSituEnvironment.list_up_jobs())
    assert_is_none(BashEnvironment.list_up_jobs())

    if not SlurmEnvironment.is_usable():
        assert_is_none(SlurmEnvironment.list_up_jobs())

    # TODO else case


# ---------------------------------------------------------- Environment methods
def test_in_situ_autorefresh():
    env = InSituEnvironment(fail_fast=True)
    assert_true(env.auto_refresh)


def test_context_is_str():
    for env_cls in DebugEnvironment, InSituEnvironment, BashEnvironment, \
                   SlurmEnvironment:
        env = env_cls()
        assert_is_instance(env.context(), str)


# ------------------------------------------------- Environment generated script
@with_setup_(prep, purge)
def script_evaluation(environment):
    print(repr(environment))  # In case of error, prints the type of environment
    lazy_computation = TestComputation().lazyfy(x1=1, x2=2)
    # TODO check computation


def test_bash_script():
    script_evaluation(BashEnvironment())


@skip_if_usuable(SlurmEnvironment)
def test_cluster_script():
    script_evaluation(SlurmEnvironment())


# ---------------------------------------------- Environment: integrated testing
# TODO how to test the logging is working correctly ?

@with_setup_(pickle_prep, pickle_purge)
def in_situ_env(environment):
    print(repr(environment)) # In case of error, prints the type of environment
    parameter_set = ParameterSet()
    parameter_set.add_parameters(x1=range(3), x2=range(3))
    experiment = Experiment(__EXP_NAME__, parameter_set,
                            TestComputation,
                            PickleStorage)
    try:
        error_code = environment.run(experiment, start=2, capacity=5)
        assert_equal(error_code, 0)
    except:
        assert_true(False, "An exception was raised by the environment")
        raise
    storage = experiment.storage
    parameters_ls, result_ls = storage.load_params_and_results()

    assert_equal(len(parameters_ls), 5)  # 5 computations
    assert_equal(len(result_ls), 5)  # 5 computations
    for parameters, result in zip(parameters_ls, result_ls):
        assert_equal(parameters["x1"] * parameters["x2"], result["mult"])


def test_in_situ_environment():
    for environment in InSituEnvironment(), InSituEnvironment(stdout=True):
        in_situ_env(environment)


@with_setup_(pickle_prep, pickle_purge)
def environment_integration(environment):
    # Can only test whether the computation was issued correctly
    print(repr(environment))  # In case of error, prints the type of environment
    parameter_set = ParameterSet()
    parameter_set.add_parameters(x1=range(3), x2=range(3))
    experiment = Experiment(__EXP_NAME__, parameter_set,
                            TestComputation,
                            PickleStorage)
    try:
        error_code = environment.run(experiment, start=2, capacity=5)
        assert_equal(error_code, 0)
    except:
        assert_true(False, "An exception was raised by the environment")
        raise


def test_bash_environment():
    for serializer in FileSerializer(), Serializer():
        environment = BashEnvironment(serializer)
        environment_integration(environment)


@skip_if_usuable(SlurmEnvironment)
def test_slurm_environment():
    environment = SlurmEnvironment(time="0:20:00", memory="1000")
    environment_integration(environment)
    # TODO how to test the code is run by slurm/sge ?


# ------------------------------------------------------------------- Serializer
@with_setup_(prep, purge)
def serializer_evaluation(serializer):
    print(repr(serializer))
    computation = TestComputation().lazyfy(x1=5, x2=10)
    computation = serializer.deserialize(serializer.serialize(computation))
    result = computation()
    print(repr(result))
    assert_equal(len(result), 1)  # only one metric
    assert_equal(result.mult, 5*10)  #  correct result


def test_serializer():
    serializer_evaluation(Serializer())


def test_file_serializer():
    serializer_evaluation(FileSerializer())


# ---------------------------------------------------------------- Customization
@with_setup(prep, purge)
def test_customization1():
    computation = TestComputation()
    computation.lazyfy(p1="1", p2=2)
    env = DebugEnvironment()
    env.add_customization({"p1": "1"}, time="1:00:00")
    env_dict = env._customize(computation, {})
    assert_equal(len(env_dict), 1)
    assert_equal(env_dict["time"], "1:00:00")


@with_setup(prep, purge)
def test_customization2():
    computation = TestComputation()
    computation.lazyfy(p1="1", p2=2)
    env = DebugEnvironment()
    env.add_customization({"p1": "1"}, time="1:00:00")
    env_dict = env._customize(computation, {"time": "2:00:00"})
    assert_equal(len(env_dict), 1)
    assert_equal(env_dict["time"], "1:00:00")


@with_setup(prep, purge)
def test_customization3():
    computation = TestComputation()
    computation.lazyfy(p1="1", p2=2)
    env = DebugEnvironment()
    env.add_customization({"p8": "1"}, time="1:00:00")
    env_dict = env._customize(computation, {"time": "2:00:00"})
    assert_equal(len(env_dict), 1)
    assert_equal(env_dict["time"], "2:00:00")


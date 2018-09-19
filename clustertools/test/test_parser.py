# -*- coding: utf-8 -*-

from argparse import Namespace
from inspect import getfullargspec

from clustertools import Experiment
from clustertools import Monitor
from clustertools.test.util_test import TestComputation, __EXP_NAME__, prep, \
    purge
from nose.tools import assert_equal, assert_raises, with_setup
from nose.tools import assert_is_none
from nose.tools import assert_true

from clustertools import ParameterSet
from clustertools.parser import *

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


def get_default(method, arg_name):
    sig = getfullargspec(method)
    print(sig)
    try:
        idx = sig.args.index(arg_name)
    except ValueError:
        return sig.kwonlydefaults[arg_name]
    n_args = len(sig.args)
    return sig.defaults[-(n_args-idx)]


# ======================================================================== Utils
def test_positive_int():
    assert_equal(5, positive_int("5"))
    assert_raises(TypeError, positive_int, "-2")
    assert_raises(TypeError, positive_int, "aaa")


def test_time_string():
    assert_equal("1:00:00", time_string("1:00:00"))
    assert_raises(TypeError, time_string, "aaa")
    assert_raises(TypeError, time_string, "23:00:00:00")
    assert_raises(TypeError, time_string, "22:65:00")


def test_or_none():
    assert_equal(5, or_none(int)(5))
    assert_equal(None, or_none(int)(None))


# ============================================================== UniversalParser
def test_universal_parser():
    uparser = UniversalParser()
    namespace = uparser.parse_args(["--capacity", "2", "--start", "10"])
    assert_equal(namespace.capacity, 2)
    assert_equal(namespace.start, 10)
    assert_true(namespace.no_fail_fast)


# ============================================================== Bash|BaseParser
def test_bash_parser_create_env():
    parser = BashParser()
    namespace = Namespace(capacity=2, no_fail_fast=True, start=0)
    env = parser.create_environment(namespace, [])
    assert_true(isinstance(env, BashEnvironment))
    assert_equal(get_default(env.run, "capacity"), 2)
    assert_equal(get_default(env.run, "start"), 0)


def test_base_parser():
    parser = BaseParser()
    parser.add_argument("custom1")
    parser.add_argument("custom2")
    environment, args = parser.parse(["custom1_value", "custom2_value",
                                      "--capacity", "1",
                                      "-s", "10",
                                      "--no_fail_fast"])
    assert_equal(args.custom1, "custom1_value")
    assert_equal(args.custom2, "custom2_value")
    assert_equal(environment.fail_fast, False)

# ========================================================== Slurm|ClusterParser
def test_slurm_parser_create_env():
    parser = SlurmParser()
    namespace = Namespace(capacity=22, no_fail_fast=True, start=10,
                          time="24:00:00", memory="4000", shell="#!bin/bash",
                          partition=None, n_proc=None, gpu=None)
    env = parser.create_environment(namespace, ["--other-flag",
                                                "--other-option=opt-value"])
    assert_true(isinstance(env, SlurmEnvironment))
    assert_equal(env.time, "24:00:00")
    assert_equal(env.memory, "4000")
    assert_is_none(env.partition)
    assert_is_none(env.n_proc)
    assert_is_none(env.gpu)

    assert_equal(env.other_flags, ["--other-flag"])
    assert_equal(env.other_options, {"--other-option": "opt-value"})

    assert_equal(get_default(env.run, "capacity"), 22)
    assert_equal(get_default(env.run, "start"), 10)


def test_parser_unkown_args():
    parser = ClusterParser()
    args, kwargs = parser.parse_unknown_args(["--other-flag",
                                              "--other-option=opt-value"])
    assert_equal(args, ["--other-flag"])
    assert_equal(kwargs, {"--other-option": "opt-value"})


def test_parse_known_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("pos1")
    parser.add_argument("--opt1")
    args, rem = parser.parse_known_args(["pos1_value",
                                         "--opt1", "opt1_value",
                                         "--unknown"])
    assert_equal(args.pos1, "pos1_value")
    assert_equal(args.opt1, "opt1_value")
    assert_equal(rem, ["--unknown"])


def test_cluster_parser():
    parser = ClusterParser()
    parser.add_argument("custom1")
    parser.add_argument("custom2")
    environment, args = parser.parse(["--capacity", "1",
                                      "-s", "10",
                                      "-t", "1:00:00",
                                      "--memory", "7231",
                                      "--partition", "luke",
                                      "--n_proc", "5",
                                      "custom1_value",
                                      "custom2_value",
                                      "--other-flag",
                                      "--other-option=opt-value"])
    assert_equal(args.custom1, "custom1_value")
    assert_equal(args.custom2, "custom2_value")
    assert_equal(environment.time, "1:00:00")
    assert_equal(environment.memory, 7231)
    assert_equal(environment.partition, "luke")
    assert_equal(environment.n_proc, 5)
    assert_equal(environment.fail_fast, True)
    assert_equal(environment.other_flags, ["--other-flag"])
    assert_equal(environment.other_options, {"--other-option": "opt-value"})


# ================================================================== DebugParser
def test_debug_parser_create_env():
    parser = DebugParser()
    namespace = Namespace(capacity=2, no_fail_fast=True, start=0,
                          verbose=True)
    env = parser.create_environment(namespace, [])
    assert_true(isinstance(env, DebugEnvironment))

    assert_true(env.print_all_parameters)

    assert_equal(get_default(env.run, "capacity"), 2)
    assert_equal(get_default(env.run, "start"), 0)


def test_debug_parser():
        parser = DebugParser()
        parser.add_argument("custom1")
        parser.add_argument("custom2")
        env, args = parser.parse(["--verbose", "--capacity", "2",
                                  "custom1_value", "custom2_value"])

        assert_true(isinstance(env, DebugEnvironment))
        assert_equal(args.custom1, "custom1_value")
        assert_equal(args.custom2, "custom2_value")
        assert_true(env.print_all_parameters)

        assert_equal(get_default(env.run, "capacity"), 2)
        assert_equal(get_default(env.run, "start"), 0)


@with_setup(prep, purge)
def test_debug_run():
    exp_name = "TestDebugParserRun"
    monitor = Monitor(exp_name)
    assert_equal(len(monitor), 0)

    parser = DebugParser()
    environment, _ = parser.parse(["--verbose"])
    parameter_set = ParameterSet()
    parameter_set.add_parameters(x1=range(3), x2=range(3))
    experiment = Experiment(exp_name, parameter_set, TestComputation)
    environment.run(experiment)

    monitor.refresh()
    assert_equal(len(monitor), 0)





# ================================================================= InSituParser
def test_insitu_parser_create_env():
    parser = InSituParser()
    namespace = Namespace(capacity=2, no_fail_fast=True, start=0,
                          stdout=True)
    env = parser.create_environment(namespace, [])
    assert_true(isinstance(env, InSituEnvironment))

    assert_true(env.stdout)

    assert_equal(get_default(env.run, "capacity"), 2)
    assert_equal(get_default(env.run, "start"), 0)


def test_insitu_parser():
        parser = InSituParser()
        parser.add_argument("custom1")
        parser.add_argument("custom2")
        env, args = parser.parse(["--stdout", "--capacity", "2",
                                  "custom1_value", "custom2_value"])

        assert_true(isinstance(env, InSituEnvironment))
        assert_equal(args.custom1, "custom1_value")
        assert_equal(args.custom2, "custom2_value")
        assert_true(env.stdout)

        assert_equal(get_default(env.run, "capacity"), 2)
        assert_equal(get_default(env.run, "start"), 0)


# ===================================================================== CTParser
def test_ct_parser_debug():
    parser = CTParser()
    parser.add_argument("custom1")
    parser.add_argument("custom2")
    env, args = parser.parse(["debug", "--verbose", "--capacity", "2",
                              "custom1_value", "custom2_value"])

    assert_true(isinstance(env, DebugEnvironment))
    assert_equal(args.custom1, "custom1_value")
    assert_equal(args.custom2, "custom2_value")
    assert_true(env.print_all_parameters)

    assert_equal(get_default(env.run, "capacity"), 2)
    assert_equal(get_default(env.run, "start"), 0)


def test_ct_parser_insitu():
    parser = CTParser()
    parser.add_argument("custom1")
    parser.add_argument("custom2")
    env, args = parser.parse(["front-end", "--stdout", "--capacity", "2",
                              "custom1_value", "custom2_value"])

    assert_true(isinstance(env, InSituEnvironment))
    assert_equal(args.custom1, "custom1_value")
    assert_equal(args.custom2, "custom2_value")
    assert_true(env.stdout)

    assert_equal(get_default(env.run, "capacity"), 2)
    assert_equal(get_default(env.run, "start"), 0)


def test_ct_parser_bash():
    parser = CTParser()
    parser.add_argument("custom1")
    parser.add_argument("custom2")
    environment, args = parser.parse(["bash", "custom1_value", "custom2_value",
                                      "--capacity", "1",
                                      "-s", "10",
                                      "--no_fail_fast"])
    assert_true(isinstance(environment, BashEnvironment))
    assert_equal(args.custom1, "custom1_value")
    assert_equal(args.custom2, "custom2_value")
    assert_equal(environment.fail_fast, False)


def test_ct_parser_slurm():
    parser = CTParser()
    parser.add_argument("custom1")
    parser.add_argument("custom2")
    environment, args = parser.parse(["slurm", "--capacity", "1",
                                      "-s", "10",
                                      "-t", "1:00:00",
                                      "--memory", "7231",
                                      "--partition", "luke",
                                      "--n_proc", "5",
                                      "custom1_value",
                                      "custom2_value",
                                      "--other-flag",
                                      "--other-option=opt-value"])
    assert_true(isinstance(environment, SlurmEnvironment))
    assert_equal(args.custom1, "custom1_value")
    assert_equal(args.custom2, "custom2_value")
    assert_equal(environment.time, "1:00:00")
    assert_equal(environment.memory, 7231)
    assert_equal(environment.partition, "luke")
    assert_equal(environment.n_proc, 5)
    assert_equal(environment.fail_fast, True)
    assert_equal(environment.other_flags, ["--other-flag"])
    assert_equal(environment.other_options, {"--other-option": "opt-value"})

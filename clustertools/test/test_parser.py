# -*- coding: utf-8 -*-
import argparse

from nose.tools import assert_equal, assert_raises
from clustertools.parser import BaseParser, ClusterParser, positive_int, \
    time_string, or_none


__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


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
    # TODO check start/capacity are OK (https://stackoverflow.com/questions/2677185/how-can-i-read-a-functions-signature-including-default-argument-values)


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
    # TODO check start/capacity are OK

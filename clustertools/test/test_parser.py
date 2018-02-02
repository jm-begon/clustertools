# -*- coding: utf-8 -*-


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
    environment, custom_options = parser.parse(["custom1", "custom2",
                                                "--capacity", "1",
                                                "-s", "10",
                                                "--no_fail_fast"])
    assert_equal(custom_options, ["custom1", "custom2"])
    assert_equal(environment.fail_fast, False)
    # TODO check start/capacity are OK (https://stackoverflow.com/questions/2677185/how-can-i-read-a-functions-signature-including-default-argument-values)


def test_cluster_parser():
    parser = ClusterParser()
    environment, custom_options = parser.parse(["--capacity", "1",
                                                "-s", "10",
                                                "-t", "1:00:00",
                                                "--memory", "7231",
                                                "--partition", "luke",
                                                "--n_proc", "5",
                                                "custom1",
                                                "custom2"])
    assert_equal(custom_options, ["custom1", "custom2"])
    assert_equal(environment.time, "1:00:00")
    assert_equal(environment.memory, 7231)
    assert_equal(environment.partition, "luke")
    assert_equal(environment.n_proc, 5)
    assert_equal(environment.fail_fast, True)
    # TODO check start/capacity are OK

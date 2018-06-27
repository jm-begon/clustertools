# -*- coding: utf-8 -*-
from contextlib import contextmanager

from nose.tools import assert_equal, assert_true

import os

from nose.tools import assert_in

from clustertools import InSituEnvironment
from clustertools.environment import SlurmEnvironment, BashEnvironment

from clustertools.config import get_ct_folder, __CT_FOLDER__, \
    __CT_FOLDER_ENVVAR__, __CT_ENVIRONMENT_ENVVARS__, get_default_environment

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


@contextmanager
def add_env(**kwargs):
    try:
        for key, val in kwargs.items():
            os.environ[key] = val
        yield
    except Exception as e:
        assert_true(False, "An exception has been raise: {}".format(repr(e)))
    finally:
        for key in kwargs:
            try:
                del os.environ[key]
            except:
                pass


def test_ct_folder():
    assert_true(get_ct_folder().endswith(__CT_FOLDER__))
    expected = "/var/test/mydata"

    with add_env(**{__CT_FOLDER_ENVVAR__: expected}):
        assert_equal(get_ct_folder(), expected)

    # Was correctly restored
    assert_true(get_ct_folder().endswith(__CT_FOLDER__))


def test_default_env():
    assert_equal(SlurmEnvironment, get_default_environment(SlurmEnvironment))
    assert_equal(InSituEnvironment, get_default_environment(InSituEnvironment))
    assert_equal(BashEnvironment, get_default_environment(BashEnvironment))

    with add_env(**{__CT_ENVIRONMENT_ENVVARS__: "insitu"}):
        assert_equal(InSituEnvironment, get_default_environment())

    with add_env(**{__CT_ENVIRONMENT_ENVVARS__: "erez"}):
        assert_in(get_default_environment(), (SlurmEnvironment,
                                              InSituEnvironment,
                                              BashEnvironment))

    expected = SlurmEnvironment if SlurmEnvironment.is_usable() \
        else InSituEnvironment

    assert_equal(get_default_environment(), expected)







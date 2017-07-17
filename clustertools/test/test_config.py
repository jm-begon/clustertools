# -*- coding: utf-8 -*-

from nose.tools import assert_equal, assert_true

import os

from clustertools.config import get_ct_folder, __CT_FOLDER__, __CT_ENV__

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


def test_ct_folder():
    assert_true(get_ct_folder().endswith(__CT_FOLDER__))
    try:
        expected = "/var/test/mydata"
        os.environ[__CT_ENV__] = expected
        assert_equal(get_ct_folder(), expected)
    finally:
        try:
            del os.environ[__CT_ENV__]
        except:
            pass

    # Was correctly restored
    assert_true(get_ct_folder().endswith(__CT_FOLDER__))


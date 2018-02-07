from nose.tools import assert_true

from clustertools import set_stdout_logging


def test_stdout_logging():
    set_stdout_logging()
    assert_true(True)  # No exception

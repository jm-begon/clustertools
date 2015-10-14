# -*- coding: utf-8 -*-

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

import os

from nose.tools import assert_in
from nose.tools import assert_equal
from nose.tools import assert_raises


from clustertools.notification import *
from clustertools.database import get_notifdb

__EXP_NAME__ = "ClustertoolsNoseTest"

def purge():
    db = get_notifdb(__EXP_NAME__)
    try:
        os.remove(db)
    except OSError:
        pass

def purge_decorator(test):
    def deco():
        purge()
        test()
        purge()
    return deco

@purge_decorator
def test_notif_update():
    pending = "test_pending"
    running = "test_running"
    completed = "test_completed"
    launchable = "test_lauchable"
    launchable1 = "test_lauchable1"
    launchable2 = "test_lauchable2"
    aborted = "test_aborted"
    aborted_except = KeyError("test_aborted")

    pending_job_update(__EXP_NAME__, pending)

    launchable_job_update(__EXP_NAME__, launchable)
    launchable_jobs_update(__EXP_NAME__, [launchable1, launchable2])

    start = running_job_update(__EXP_NAME__, running)
    completed_job_update(__EXP_NAME__, completed, start)
    aborted_job_update(__EXP_NAME__, aborted, start, aborted_except)

    histo = Historic(__EXP_NAME__, None)

    assert_in(pending, histo.pending_jobs().keys())

    assert_in(completed, histo.done_jobs().keys())
    assert_in(launchable, histo.launchable_jobs().keys())
    assert_in(pending, histo.pending_jobs().keys())
    assert_in(launchable1, histo.launchable_jobs().keys())
    assert_in(launchable2, histo.launchable_jobs().keys())
    assert_in(aborted, histo.aborted_jobs().keys())

    # Running has been set to launchable
    assert_in(running, histo.launchable_jobs().keys())

    assert_equal(histo.is_launchable(pending), False)
    assert_equal(histo.is_launchable(completed), False)
    assert_equal(histo.is_launchable(aborted), False)

    assert_equal(histo.is_launchable(running), True)
    assert_equal(histo.is_launchable(launchable), True)
    assert_equal(histo.is_launchable(launchable1), True)
    assert_equal(histo.is_launchable(launchable2), True)





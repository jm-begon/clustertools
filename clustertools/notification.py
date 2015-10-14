# -*- coding: utf-8 -*-

"""
Module :mod:`notification` manages the notification system.

Convention
----------
A computaiton absent from the notification db is considered in launchable state.
This avoid a useless call to the notification db

Note
----
A running job aborted for uncatchable reasons will stay in running state
although it is not running any longer. Refresh the historic to get it right
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

import os
from datetime import datetime

from clusterlib.scheduler import queued_or_running_jobs

from .database import update_notification, load_notifications, load_experiments


__RUNNING__ = "RUNNING"
__COMPLETED__ = "COMPLETED"
__ABORTED__ = "ABORTED"
__PENDING__ = "PENDING"
__LAUNCHABLE__ = "LAUNCHABLE"

__STATE__= "STATE"
__DATE__ = "date"
__DURATION__ = "duration"
__EXCEPT__ = "exception"


#======================= STATUS UPDATE =======================#
def launchable_job_update(exp_name, comp_name):
    now = datetime.now()
    d = {
        __STATE__: __LAUNCHABLE__,
        __DATE__: now,
    }
    update_notification(exp_name, {comp_name : d})
    return now

def launchable_jobs_update(exp_name, comp_names):
    now = datetime.now()
    dictionary = {
        comp_name:
        {
            __STATE__:__LAUNCHABLE__,
            __DATE__: now
        }
        for comp_name in comp_names
    }
    update_notification(exp_name, dictionary)
    return now

def pending_job_update(exp_name, comp_name):
    now = datetime.now()
    d = {
        __STATE__: __PENDING__,
        __DATE__: now,
    }
    update_notification(exp_name, {comp_name : d})
    return now

def running_job_update(exp_name, comp_name):
    now = datetime.now()
    d = {
        __STATE__: __RUNNING__,
        __DATE__: now
    }
    update_notification(exp_name, {comp_name : d})
    return now


def completed_job_update(exp_name, comp_name, startdate):
    now = datetime.now()
    d = {
        __STATE__: __COMPLETED__,
        __DATE__: now,
        __DURATION__: str(now - startdate)
    }
    update_notification(exp_name, {comp_name : d})
    return now

def aborted_job_update(exp_name, comp_name, startdate, exception):
    now = datetime.now()
    d = {
        __STATE__: __ABORTED__,
        __DATE__: now,
        __DURATION__: (now - startdate).total_seconds(),
        __EXCEPT__: exception
    }
    update_notification(exp_name, {comp_name : d})
    return now


#======================= LOOKUPS =======================#

def _sort_by_state(dico):
    sorted = {}
    for k, v in dico.iteritems():
        state_dict = sorted.get(v[__STATE__])
        if state_dict is None:
            state_dict = {}
            sorted[v[__STATE__]] = state_dict
        state_dict[k] = v
    return sorted

def is_up(status):
    return (status == __COMPLETED__ or status == __RUNNING__
            or status == __PENDING__)

def _filter(job_dict, status):
    return {k:v for k,v in job_dict.iteritems() if v[__STATE__] == status}

class Historic(object):
    """
    job_dict : mapping {comp_name -> mapping}
    state_dict: mapping {state -> job_dict}
    """
    def __init__(self, exp_name=None, user=os.environ["USER"]):
        self.exp_name = exp_name
        self.job_dict = {}
        self.state_dict = {}
        self.user = user
        self.refresh()

    def refresh(self):
        if self.exp_name is None:
            job_dict = {}
            exps = load_experiments()
            for exp in exps.keys():
                job_dict.update(load_notifications(exp))
        else:
            job_dict = load_notifications(self.exp_name)

        # Updating the false running jobs
        r_jobs = _filter(job_dict, __RUNNING__)
        queued = frozenset(queued_or_running_jobs(self.user))
        launchables = {k for k in r_jobs.keys() if k not in queued}
        launchable_jobs_update(self.exp_name, launchables)
        # +--- Applying local change
        for comp_name in launchables:
            info = job_dict[comp_name]
            info[__STATE__] = __LAUNCHABLE__

        # Setting the refreshment
        self.job_dict = job_dict
        self.state_dict = _sort_by_state(self.job_dict)

    def __len__(self):
        return len(self.job_dict)


    def done_jobs(self):
        return _filter(self.job_dict, __COMPLETED__)
    def pending_jobs(self):
        return _filter(self.job_dict, __PENDING__)
    def running_jobs(self):
        return _filter(self.job_dict, __RUNNING__)
    def aborted_jobs(self):
        return _filter(self.job_dict, __ABORTED__)
    def launchable_jobs(self):
        return _filter(self.job_dict, __LAUNCHABLE__)

    def get_state(self, comp_name):
        info = self.job_dict.get(comp_name)
        if info is None:
            return __LAUNCHABLE__
        else:
            return info[__STATE__]

    def already_up(self, comp_name=None):
        if comp_name is None:
            return {k:v for k,v in self.job_dict.iteritems()
                    if is_up(v[__STATE__])}



        state = self.get_state(comp_name)

        return is_up(state)

    def is_launchable(self, comp_name):
        state = self.get_state(comp_name)

        if state == __ABORTED__:
            logger = logging.getLogger("clustertools")
            logger.warn("Computation '%s' is in aborted state." % comp_name)

        return state == __LAUNCHABLE__

    def count_by_state(self):
        return {k:len(v) for k,v in self.state_dict.iteritems()}


    def aborted_to_launchable(self):
        for comp_name in self.aborted_jobs().keys():
            launchable_job_update(self.exp_name, comp_name)



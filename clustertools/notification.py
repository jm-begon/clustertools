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
import getpass
from datetime import datetime
import logging

from clusterlib.scheduler import queued_or_running_jobs

from .database import get_storage, load_notifications


__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

__RUNNING__ = "RUNNING"
__COMPLETED__ = "COMPLETED"
__ABORTED__ = "ABORTED"
__PENDING__ = "PENDING"
__LAUNCHABLE__ = "LAUNCHABLE"
__PARTIAL__ = "PARTIAL"
__INCOMPLETE__ = "INCOMPLETE"
__CRITICAL__ = "CRITIC"

__STATE__= "STATE"
__DATE__ = "date"
__LASTSAVE__ = "last save"
__DURATION__ = "duration"
__EXCEPT__ = "exception"


# ======================= STATUS UPDATE ======================= #
def launchable_job_update(exp_name, comp_name):
    now = datetime.now()
    d = {
        __STATE__: __LAUNCHABLE__,
        __DATE__: now,
    }
    get_storage(exp_name).update_notification(comp_name, {comp_name : d})
    return now


def launchable_jobs_update(exp_name, comp_names):
    now = datetime.now()
    dictionaries = [{comp_name:
        {
            __STATE__:__LAUNCHABLE__,
            __DATE__: now
        }}
        for comp_name in comp_names
    ]
    get_storage(exp_name).update_notifications(comp_names, dictionaries)
    return now


def pending_job_update(exp_name, comp_name):
    now = datetime.now()
    d = {
        __STATE__: __PENDING__,
        __DATE__: now,
    }
    get_storage(exp_name).update_notification(comp_name, {comp_name : d})
    return now


def running_job_update(exp_name, comp_name):
    now = datetime.now()
    d = {
        __STATE__: __RUNNING__,
        __DATE__: now
    }
    get_storage(exp_name).update_notification(comp_name, {comp_name : d})
    return now


def partial_job_update(exp_name, comp_name, startdate):
    now = datetime.now()
    d = {
        __STATE__: __PARTIAL__,
        __DATE__: startdate,
        __LASTSAVE__: now
    }
    get_storage(exp_name).update_notification(comp_name, {comp_name : d})
    return now


def completed_job_update(exp_name, comp_name, startdate):
    now = datetime.now()
    d = {
        __STATE__: __COMPLETED__,
        __DATE__: now,
        __DURATION__: str(now - startdate)
    }
    get_storage(exp_name).update_notification(comp_name, {comp_name : d})
    return now


def critical_job_update(exp_name, comp_name, startdate):
    now = datetime.now()
    d = {
        __STATE__: __CRITICAL__,
        __DATE__: now,
        __DURATION__: str(now - startdate)
    }
    get_storage(exp_name).update_notification(comp_name, {comp_name : d})
    return now


def aborted_job_update(exp_name, comp_name, startdate, exception):
    now = datetime.now()
    d = {
        __STATE__: __ABORTED__,
        __DATE__: now,
        __DURATION__: (now - startdate).total_seconds(),
        __EXCEPT__: exception
    }
    get_storage(exp_name).update_notification(comp_name, {comp_name : d})
    return now


def aborted_jobs_update(exp_name, comp_names, exception):
    now = datetime.now()
    dictionaries = [{comp_name:
        {
            __STATE__:__ABORTED__,
            __DATE__:now,
            __EXCEPT__:exception

         }}
        for comp_name in comp_names
    ]
    get_storage(exp_name).update_notifications(comp_names, dictionaries)
    return now


def incomplete_job_update(exp_name, comp_name, startdate):
    now = datetime.now()
    d = {
        __STATE__: __INCOMPLETE__,
        __DATE__: startdate,
        __LASTSAVE__: now
    }
    get_storage(exp_name).update_notification(comp_name, {comp_name : d})
    return now


def incomplete_jobs_update(exp_name, comp_names):
    now = datetime.now()
    dictionaries = [{comp_name:
        {
            __STATE__:__INCOMPLETE__,
            __DATE__: now
        }}
        for comp_name in comp_names
    ]
    get_storage(exp_name).update_notifications(comp_names, dictionaries)
    return now

# ======================= LOOKUPS ======================= #


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
            or status == __PENDING__ or status == __PARTIAL__)


def _filter(job_dict, status):
    return {k:v for k,v in job_dict.iteritems() if v[__STATE__] == status}


class Historic(object):
    """
    job_dict : mapping {comp_name -> mapping}
    state_dict: mapping {state -> job_dict}
    """
    def __init__(self, exp_name, user=getpass.getuser()):
        self.exp_name = exp_name
        self.job_dict = {}
        self.state_dict = {}
        self.user = user
        self.storage = get_storage(self.exp_name)
        self.refresh()

    def refresh(self):
        job_dict = load_notifications(self.exp_name)

        # Updating the false running jobs
        queued = frozenset(queued_or_running_jobs(self.user))
        r_jobs = _filter(job_dict, __RUNNING__)
        p_jobs = _filter(job_dict, __PENDING__)
        i_jobs = _filter(job_dict, __PARTIAL__)
        launchables = {k for k in r_jobs.keys() if k not in queued}
        launchables.update({k for k in p_jobs.keys() if k not in queued})
        launchable_jobs_update(self.exp_name, launchables)
        incompletes = {k for k in i_jobs.keys() if k not in queued}
        incomplete_jobs_update(self.exp_name, incompletes)
        # +--- Applying local change
        for comp_name in launchables:
            info = job_dict[comp_name]
            info[__STATE__] = __LAUNCHABLE__
        for comp_name in incompletes:
            info = job_dict[comp_name]
            info[__STATE__] = __INCOMPLETE__

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
    def partial_jobs(self):
        return _filter(self.job_dict, __PARTIAL__)
    def incomplete_jobs(self):
        return _filter(self.job_dict, __INCOMPLETE__)
    def critical_jobs(self):
        return _filter(self.job_dict, __CRITICAL__)

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
            logger.info("Computation '%s' is in aborted state." % comp_name)
        if state == __INCOMPLETE__:
            logger = logging.getLogger("clustertools")
            logger.info("Computation '%s' is in incomplete state." % comp_name)

        return state == __LAUNCHABLE__

    def count_by_state(self):
        return {k:len(v) for k,v in self.state_dict.iteritems()}

    def to_launchable(self, comp_name):
        launchable_job_update(self.exp_name, comp_name)

    def aborted_to_launchable(self, filter_dict=None):
        filter_lambda = (lambda x:True) if filter_dict is None else \
            (lambda x:x in filter_dict)
        aborted = [x for x in self.aborted_jobs().keys() if filter_lambda(x)]
        launchable_jobs_update(self.exp_name, aborted)

    def not_completed_to_aborted(self, comp_names):
        completed = self.done_jobs().keys()
        comp_names = [comp_name for comp_name in comp_names
                      if comp_name not in completed]
        aborted_jobs_update(self.exp_name, comp_names, Exception('Force statis'))



    def pending_to_launchable(self):
        launchable_jobs_update(self.exp_name, self.pending_jobs().keys())

    def incomplete_to_launchable(self):
        launchable_jobs_update(self.exp_name, self.incomplete_jobs().keys())

    def critical_to_launchable(self):
        launchable_jobs_update(self.exp_name, self.critical_jobs().keys())

    def reset(self, *comp_names):
        if len(comp_names) > 0:
            for comp_name in comp_names:
                launchable_job_update(self.exp_name, comp_name)
        else:
            launchable_jobs_update(self.exp_name, self.job_dict.keys())

    def print_log(self, comp_name, last_lines=None):
        get_storage(self.exp_name).print_log(comp_name, last_lines=last_lines)


def yield_not_done_computation(experiment, user=None):
    if user is None:
        user = getpass.getuser()
    historic = Historic(experiment.name, user)
    for comp_name, param in experiment:
        if historic.is_launchable(comp_name):
            yield comp_name, param

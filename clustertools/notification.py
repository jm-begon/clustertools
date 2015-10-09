# -*- coding: utf-8 -*-

"""
Module :mod:`notification` manages the notification system.
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

from datetime import datetime

from .database import update_notification, load_notifications, load_experiments


__RUNNING__ = "RUNNING"
__COMPLETED__ = "COMPLETED"
__ABORTED__ = "ABORTED"
__PENDING__ = "PENDING"
__STATE__= "STATE"


#======================= STATUS UPDATE =======================#

def pending_job_update(exp_name, comp_name):
    now = datetime.now()
    d = {
        __STATE__: __PENDING__,
        "date": now,
    }
    update_notification(exp_name, {comp_name : d})
    return now

def running_job_update(exp_name, comp_name):
    now = datetime.now()
    d = {
        __STATE__: __RUNNING__,
        "date": now
    }
    update_notification(exp_name, {comp_name : d})
    return now

def completed_job_update(exp_name, comp_name, startdate):
    now = datetime.now()
    d = {
        __STATE__: __COMPLETED__,
        "date": now,
        "duration": str(now - startdate)
    }
    update_notification(exp_name, {comp_name : d})
    return now

def aborted_job_update(exp_name, comp_name, startdate, exception):
    now = datetime.now()
    d = {
        __STATE__: __ABORTED__,
        "date": now,
        "duration": (now - startdate).total_seconds(),
        "exception": exception
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

class Historic(object):
    def __init__(self, exp_name=None):
        self.exp_name = exp_name
        self.job_dict = None
        self.state_dict = None
        self.refresh()

    def refresh(self):
        if self.exp_name is None:
            self.job_dict = {}
            exps = load_experiments()
            for exp in exps.keys():
                self.job_dict.update(load_notifications(exp))
        else:
            self.job_dict = load_notifications(self.exp_name)
        self.state_dict = _sort_by_state(self.job_dict)

    def __len__(self):
        return len(self.job_dict)

    def filter(self, status):
        return {k:v for k,v in self.job_dict.iteritems()
                if v[__STATE__] == status}

    def done_jobs(self):
        return self.filter(__COMPLETED__)
    def pending_jobs(self):
        return self.filter(__PENDING__)
    def running_jobs(self):
        return self.filter(__RUNNING__)
    def aborted_jobs(self):
        return self.filter(__ABORTED__)

    def already_up(self):
        return {k:v for k,v in self.job_dict.iteritems()
                if is_up(v[__STATE__])}


    def count_by_state(self):
        return {k:len(v) for k,v in self.state_dict.iteritems()}

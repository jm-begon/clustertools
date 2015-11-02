# -*- coding: utf-8 -*-

"""
Module :mod:`util` is a set of misc. functions
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

import os
import shutil
import json
from inspect import getargspec
from copy import copy
from hashlib import sha256
from datetime import datetime



__CT_FOLDER__ = "clustertools_data"
__LOG_ENV__ = "CLUSTERTOOLS_LOGS_FOLDER"
__METALOG__ = "clustertools.log"

def get_ct_folder():
    return os.path.join(os.environ["HOME"], __CT_FOLDER__)

def get_log_folder(exp_name=None):
    try:
        folder = os.environ[__LOG_ENV__]
    except KeyError:
        folder = os.path.join(get_ct_folder(), "logs")
        os.environ[__LOG_ENV__] = folder

    if exp_name is not None:
        folder = os.path.join(folder, exp_name)

    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def get_meta_log_file():
    fname = "clustertools_%s.log" % (datetime.now().strftime("%B%Y"))
    return os.path.join(get_log_folder(), fname)

def get_log_file(exp_name, comp_name):
    folder = get_log_folder(exp_name)
    for fname in os.listdir(folder):
        fp = os.path.join(folder, fname)
        if os.path.isfile(fp) and fname.startswith(comp_name+".") and fname.endswith(".txt"):
            return fp

def purge_logs(exp_name, comp_name=None):
    if comp_name is None:
        shutil.rmtree(get_log_folder(exp_name))
    else:
        fp = get_log_file(exp_name, comp_name)
        if fp is not None:
            os.remove(fp)


def kw_intersect(function, dictionary, *args, **kwargs):
    """
    Computes the intersection between the function's parameters and
    the given dictionary
    Parameters
    ----------
    function : callable
        The function to process
    dictionary : dict
        The dictionary to process
    args : list
        The list of positional arguments
    kwargs : dict
        The keyword arguments
    Return
    ------
    intersect_dict : dict
        The intersection between the function's parameters and the given
        dictionary
    """
    try:
        prototype = getargspec(function)
    except TypeError:
        # In case of a class
        prototype = getargspec(function.__init__)

    # If function as a **kwargs, it will swallow all the extra arguments
    if prototype.keywords is not None and len(args) == 0:
        return dictionary
    # Intersecting dictionaries
    sub_dict = dict()
    func_args = prototype.args
    for i, key in enumerate(func_args):
        if i >= len(args):
            if key in dictionary:
                sub_dict[key] = dictionary[key]
            if key in kwargs:
                sub_dict[key] = kwargs[key]
    return sub_dict

def call_with(function, dictionary, *args, **kwargs):
    """
    Call the given function with the given dictionary with the additional
    supplied arguments
    Parameters
    ----------
    function : callable
        The function to process
    dictionary : dict
        The dictionary to process
    args : list
        The list of positional arguments
    kwargs : dict
        The keyword arguments
    Return
    ------
    The result of the function with the given sefely inputs
    """
    return function(*args, **kw_intersect(function, dictionary, *args, **kwargs))

def encode_kwargs(dictionary):
    s = json.dumps(dictionary)
    s = s.replace("'", "\\'")
    return s.replace('"', '\\"')

def decode_kwargs(string):
    return json.loads(string)

def bash_submit(job_command, job_name, shell_script="#!/bin/bash"):
    return (u"echo '%s\n%s' | bash" % (shell_script, job_command))

def false_submit(job_command, job_name, shell_script="#!/bin/bash"):
    return (u"echo '%s'" % job_name)


def experiment_diff(experiment, computations={}, scheduled=[]):
    """
    computations: in-able of comp_name
    scheduled: in-able of comp_name
    """
    res = []
    for label, params in experiment:
        if label not in computations and label not in scheduled:
            res.append((label, params))
    return res

def running_job_diff(exp_name, user=None):
    histo = Historic(exp_name)
    r_notif = set(histo.running_jobs().keys())
    r_backend = {j for j in queued_or_running_jobs(user)
                    if j.find(exp_name) >= 0}
    notif_only = r_notif.difference(r_backend)
    backend_only = r_backend.difference(notif_only)
    both = r_notif.intersection(r_backend)
    return {"Notif-only":notif_only, "Backend-only":backend_only, "Both":both}


def reorder(ls, indices, in_place=False):
    if in_place:
        tmps = [ls[i] for i in indices]
        for i, idx in enumerate(tmps):
            ls[i] = idx
        res = ls

    else:
        res = copy(ls)
        for i, idx in enumerate(indices):
            res[i] = ls[idx]
    try:
        return res[:len(indices)]
    except:
        return res


def hashlist(ls):
    return sha256(str(ls)).digest()

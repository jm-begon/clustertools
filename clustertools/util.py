# -*- coding: utf-8 -*-

"""
Module :mod:`util` is a set of misc. functions
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

import json
from inspect import getargspec


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


def experiment_diff(experiment, computations):
    """
    computations: mapping: computation_name --> list of parameters
        from Experiment
    """
    res = []
    for label, params in experiment:
        if not computations.has_key(label):
            res.append((label, params))
    return res

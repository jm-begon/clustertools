# -*- coding: utf-8 -*-

"""
Module :mod:`util` is a set of misc. functions
"""

from inspect import getargspec
from copy import copy
from hashlib import sha256
import warnings
import functools


__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


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
    # TODO getargspec deprecated in Python
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
    return function(*args, **kw_intersect(function,
                                          dictionary,
                                          *args,
                                          **kwargs))


def escape(s):
    return s.replace("'", "\\\'").replace('"', '\\\"').replace(" ", "\\ ")\
        .replace("(", "\\(").replace(")", "\\)")


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


# from http://stackoverflow.com/questions/2536307/decorators-in-the-python-standard-lib-deprecated-specifically
def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning, stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)

    return new_func

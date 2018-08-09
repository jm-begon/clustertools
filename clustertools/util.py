# -*- coding: utf-8 -*-

"""
Module :mod:`util` is a set of misc. functions
"""
import inspect
import os
import signal
from contextlib import contextmanager
from inspect import getargspec
from copy import copy
from hashlib import sha256
import warnings
import functools

import logging

import sys

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


def call_with(function, dictionary, **kwargs):
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
    parameters = inspect.signature(function).parameters
    d = {k: v for k, v in dictionary.items()}
    d.update(**kwargs)

    if inspect.Parameter.VAR_KEYWORD in [x.kind for x in
                                         list(parameters.values())]:
        # If function as a **kwargs, it will swallow all the extra arguments
        return function(**d)

    return function(**{k: v for k, v in d.items() if k in parameters})


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
    return sha256(str(ls).encode("utf-8")).digest()


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


class SignalExecption(RuntimeError):
    def __init__(self, sig_num, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sig_num = sig_num


class SigHandler(object):
    """
    Constructor parameter
    ---------------------
    callback: callable(exception) -> None
        The callback to handle signal
    """
    def __init__(self, callback):
        self.callback = callback
        self.backups = {
            signal.SIGINT: signal.getsignal(signal.SIGINT),
            signal.SIGTERM: signal.getsignal(signal.SIGTERM)
        }

    def _callback(self, signalnum, frame):
        exception = SignalExecption(signalnum,
                                    "Got signal {} in frame "
                                    "{}".format(signalnum,
                                                repr(frame)))
        self.callback(exception)
        self._restore()
        os.kill(os.getpid(), signalnum)

    def _restore(self):
        for sig_num, handler in self.backups.items():
            try:
                signal.signal(sig_num, handler)
            except ValueError:
                # ValueError is raised if signal.signal(...) is not called
                # from the main thread
                pass

    def __enter__(self):
        self.backups = {s: signal.getsignal(s) for s in self.backups}

        for sig_num in self.backups:
            try:
                signal.signal(sig_num, self._callback)
            except ValueError:
                # ValueError is raised if signal.signal(...) is not called
                # from the main thread
                pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, KeyboardInterrupt) or \
                isinstance(exc_val, SystemExit):
            # KeyboardInterrupt cannot be raised through a SIGINT since its
            # handler has been modified
            self.callback(exc_val)

        self._restore()


@contextmanager
def catch_logging():
    # Memo
    logger = logging.getLogger("clustertools")
    handlers = logger.handlers
    level = logger.level
    # New stuff
    logger.handlers = []
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    logger.addHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                  "%(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)

    try:
        yield
    finally:
        logger.handlers = handlers
        logger.level = level
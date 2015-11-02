# -*- coding: utf-8 -*-

"""
============
clustertools
============
:mod:`clustertools` is a toolkit to run experiments on supercomputers.
It is built on top of clusterlib (https://github.com/clusterlib/clusterlib).

TODO
clustertools_db
clustertools_logs
notification system

Logging
=======
This library uses logging for
    - Warning in :func:`experiment.run_experiment` ('clustertools')
By default, logging is disabled
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"
__version__ = '0.0.1'
__date__ = "08 Oct. 2015"


from .database import load_experiments, reset_experiment
from .notification import Historic
from .experiment import (Computation, Experiment, Hasher, Result,
                         build_result_cube)
from .parser import parse_args, parse_params
from .runner import run_experiment
from .util import (get_log_folder, get_log_file, purge_logs, call_with,
                   encode_kwargs, decode_kwargs, bash_submit,false_submit,
                   experiment_diff, reorder, get_meta_log_file)

__all__ = ["load_experiments", "reset_experiment", "Historic", "Computation",
           "Experiment", "build_result_cube", "Hasher", "Result", "run_experiment",
           "relaunch_experiment", "get_log_folder", "parse_args", "parse_params",
           "get_log_folder", "get_log_file", "purge_logs", "call_with",
           "encode_kwargs", "decode_kwargs", "bash_submit", "false_submit",
           "experiment_diff", "set_stdout_logging", "reorder"]




import logging
logging.getLogger("clustertools").addHandler(logging.NullHandler())

def set_stdout_logging():
    """
    Sets stdout as default logging facility
    """
    import sys
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)

    fh = logging.FileHandler(get_meta_log_file())
    fh.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                  "%(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger = logging.getLogger("clustertools")
    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)

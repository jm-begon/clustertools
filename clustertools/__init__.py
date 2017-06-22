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

File system
===========
By default everything related to clustertools is located in a folder named
'clustertools_data' (aka ct_folder) in the user home directory. The ct_folder
is structured as followed:
    clustertools_data
    |- logs
    |- exp_XXX
    |   |- logs
    |   |- $result$
    |   |- $notifs$
    |- exp_YYY
        |...
where logs is a folder containing the main logs (not the one corresponding to
the experiments). exp_XXX is the folder related to experiment 'XXX'.

Logging
=======
This library uses logging for
    - Warning in :func:`experiment.run_experiment` ('clustertools')
By default, logging is disabled
"""


from .notification import Historic
from .storage import Architecture
from .experiment import (Computation, PartialComputation, Experiment, Hasher,
                         Datacube, build_result_cube, build_datacube)
from .parser import parse_args, parse_params
from .runner import run_experiment
from .util import (call_with, encode_kwargs, decode_kwargs, bash_submit,
                   false_submit, experiment_diff, reorder)
from .config import get_ct_folder


__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"
__version__ = '0.1.0'
__date__ = "08 Oct. 2015"


__all__ = [ "Historic", "Computation",
            "PartialComputation", "Experiment", "build_result_cube", "Hasher",
            "Datacube", "run_experiment", "relaunch_experiment",
            "parse_args", "parse_params", "call_with", "encode_kwargs",
            "decode_kwargs", "bash_submit", "false_submit", "experiment_diff",
            "set_stdout_logging", "reorder", "get_ct_folder"]


import logging
logging.getLogger("clustertools").addHandler(logging.NullHandler())


def set_stdout_logging(architecture=Architecture()):
    """
    Sets stdout as default logging facility
    """
    import sys
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)

    fh = logging.FileHandler(architecture.get_meta_log_file())
    fh.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                  "%(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger = logging.getLogger("clustertools")
    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)

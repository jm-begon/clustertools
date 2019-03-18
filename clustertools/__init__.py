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
import logging

# Clustertools visibility
from .storage import Architecture
from .state import Monitor
from .experiment import Computation, ParameterSet, ConstrainedParameterSet, \
    PrioritizedParamSet, Result, Experiment
from .environment import Serializer, FileSerializer, InSituEnvironment
from .datacube import Datacube, build_result_cube, build_datacube
from .parser import BaseParser, ClusterParser, CTParser
from .util import call_with
from .config import get_ct_folder, get_default_environment


__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"
__version__ = '0.1.3'
__date__ = "08 Oct. 2015"


__all__ = ["Monitor", "Computation", "ParameterSet", "ConstrainedParameterSet",
           "Result", "Experiment", "Serializer", "FileSerializer" "Datacube",
           "build_result_cube", "build_datacube", "BaseParser", "ClusterParser",
           "call_with", "set_stdout_logging", "InSituEnvironment",
           "get_default_environment", "CTParser"]


logging.getLogger("clustertools").addHandler(logging.NullHandler())


def shutup_logger():
    logging.getLogger("clustertools").addHandler(logging.NullHandler())


def set_stdout_logging(log_level=logging.DEBUG, architecture=Architecture()):
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
    logger.setLevel(log_level)

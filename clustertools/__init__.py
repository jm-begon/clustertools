# -*- coding: utf-8 -*-

"""
============
clustertools
============
:mod:`clustertools` is a toolkit to run experiments on supercomputers.
It is built on top of clusterlib (https://github.com/clusterlib/clusterlib).


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
from .experiment import Computation, Experiment, run_experiment
from .parser import parse_args
from .util import call_with, encode_kwargs, decode_kwargs, bash_submit

__all__ = ["load_experiments", "reset_experiment", "Historic", "Computation",
           "Experiment", "run_experiment", "parse_args", "call_with",
           "encode_kwargs", "decode_kwargs", "set_stdout_logging",
           "bash_submit"]




import logging
logging.getLogger("clustertools").addHandler(logging.NullHandler())

def set_stdout_logging():
    """
    Sets stdout as default logging facility
    """
    import sys
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                  "%(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger = logging.getLogger("clustertools")
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)

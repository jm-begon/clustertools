# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
This example illustrates how to set up a computation template
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

import time
from random import randint

from clustertools import Computation, call_with

def dummy_func1(x, y=2):
    return x*y

def dummy_func2(z, w):
    return z+w

class BasicComputation(Computation):

    def run(self, **parameters):
        time.sleep(randint(1, 10))
        results = {}
        results["f1"] = call_with(dummy_func1, parameters)
        results["f2"] = call_with(dummy_func2, parameters)
        return results


if __name__ == "__main__":
    """
    Basic experiment

    Command line parameters
    -----------------------
    sys.argv[1]: string
        Experiment name
    sys.argv[2]: string
        Computation name
    sys.argv[3]: Json string
        The hyperparameters of the computation
    """
    import sys, json

    if len(sys.argv) != 4:
        raise AssertionError("Expected 4 parameters, got "+str(len(sys.argv)))
    else:
        exp_name = sys.argv[1]
        comp_name = sys.argv[2]
        comp_params = json.loads(sys.argv[3])
        computation = BasicComputation(exp_name, comp_name)
        computation(**comp_params)



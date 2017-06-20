# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
This example illustrates how to set up a computation template
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


from clustertools import Computation



class BasicComputation(Computation):

    def run(self, **parameters):
        results = {}
        results["mult"] = parameters["a"] * parameters["b"]
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



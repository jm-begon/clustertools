# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
This example illustrates a simple launcher working with bash
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

from clustertools import Experiment, run_experiment, bash_submit
from clustertools import set_stdout_logging

if __name__ == "__main__":
    set_stdout_logging()
    experiment = Experiment("basic")
    experiment.add_params(x=[1, 2], z=4)
    experiment.add_params(w=[5, 6], x=3)
    run_experiment(experiment, "basic_exp.py", bash_submit)





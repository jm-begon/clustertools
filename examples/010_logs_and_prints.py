# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
When running computations on the background or through a scheduler such as
Slurm, print statement are lost. Although you can redirect the standard outputs
in the former case, the procedure is not as straightforward in the latter case.

Fortunately, Clustertools offers a unify way of managing such things by creating
a log file in a standard fashion (independent of the environment/backend).

The `clustertools` utility offers a simple way to get the log of each
computation. Simply run `clustertools display log <exp_name> <comp_number>`.

1. Run `python 000_reset.py` to reset the experiment.
2. Run `python 010_logs_and_prints.py front-end`
3. Run `clustertools display log BasicUsage 0` to print the log

You can play with the computation number
"""

from clustertools import Computation, CTParser, ParameterSet, \
    Experiment, set_stdout_logging


class MyComputation(Computation):
    """
    Inherit from `Computation` and redefine the `run` method as you which
    """

    def run(self, collector, x, z, w, y=2, **parameters):
        import time
        from datetime import datetime
        from random import randint

        # We add a few print statements
        print(repr(self))
        print()
        print("{}: I must multiply {} by {}. This is a hard computation, "
              "it will take a few seconds".format(datetime.now(), x, y))
        collector["multiply"] = x * y
        time.sleep(randint(1, 10))

        print("{}: Now I must add {} and {}. This is easier but I am tired "
              "with all those hard computations. Let me think..."
              "".format(datetime.now(), z, w))
        collector["sum"] = z + w
        time.sleep(randint(1, 10))

        print("{}: Woah, it was hard. I think I'll go back to sleep."
              "".format(datetime.now()))


if __name__ == "__main__":
    set_stdout_logging()

    parser = CTParser()

    environment, _ = parser.parse()

    param_set = ParameterSet()
    param_set.add_parameters(x=[1, 2, 3], z=4, w=[5, 6])

    experiment = Experiment("BasicUsage", param_set, MyComputation)

    environment.run(experiment)



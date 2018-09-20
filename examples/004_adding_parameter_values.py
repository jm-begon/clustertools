# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Go through `001_basic_usage.py` before running this example. We will re-use
the same computation: x*y and z+w for x in [1, 2, 3], y = 2, z = 4,
w in [5, 6] in an experiment called BasicUsage.

Suppose you have done your experiment (say running `001_basic_usage.py`) and
you suddenly wanted to measure the influence of a new parameter values. Say
x=4. Of course, you cannot just add it to the parameter set and run the
computation again: Clustertools will mix and match the parameter ordering and
you will end up with a messy mess.

But don't give up! There is a simple way. You just have to edit your .py file
and explicitely tell Clustertools that you are adding new parameters. After
that you can just relaunch the experiment.

Changes to `001_basic_usage.py` are minimal:

In the former case, you have to
  1. Add a separator to the `ParameterSet` instance, thanks to the
  :meth:`add_separator` method.
  2. Add the new parameter values after the separator.

Adding the separator will tell Clustertools that it is supposed to run the
combination of parameters before the separator before running the
combinations relating to the new value(s). You can of course use several
separators.

Note that you can use the separators to influence the ordering the computations.
But there is a dedicated way to do that (see `007_priority.py`).

Do `python 001_basic_usage.py front-end`. Since the experiment `BasicUsage` has
already run, you cannot adapt it directly. Now imagine that you modified
`001_basic_usage.py` as this file and run it
(`python 004_adding_parameter_values.py front-end`). You can then run
`002_results.py` to see how the datacube has evolved.
"""


from clustertools import Computation, CTParser, ParameterSet, \
    Experiment, set_stdout_logging


class MyComputation(Computation):
    """
    Inherit from `Computation` and redefine the `run` method as you which
    """

    def run(self, result, x, z, w, y=2, **parameters):
        import time
        from random import randint

        result["multiply"] = x * y
        result["sum"] = z + w
        time.sleep(randint(1, 10))


if __name__ == "__main__":
    set_stdout_logging()

    parser = CTParser()

    environment, _ = parser.parse()

    param_set = ParameterSet()
    param_set.add_parameters(x=[1, 2, 3], z=4, w=[5, 6])

    # Add the separator and the new parameter values
    # -- Separator
    param_set.add_separator()
    # -- new parameter values
    param_set.add_parameters(x=4)
    # you could also have added several values at once with:
    # param_set.add_parameters(x=[4, 5]) for instance

    experiment = Experiment("BasicUsage", param_set, MyComputation)
    environment.run(experiment)

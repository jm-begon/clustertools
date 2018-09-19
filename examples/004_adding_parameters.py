# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Go through `001_basic_usage.py` before running this example. We will re-use
the same computation: x*y and z+w for x in [1, 2, 3], y = 2, z = 4,
w in [5, 6] in a experiment called BasicUsage.

Suppose you have done your experiment (say running `001_basic_usage.py`) and
you suddenly wanted measure the influence of a new parameter. Of course,
you cannot just add it to the parameter set and run the computation again:
Clustertools will mix and match the parameter ordering and you will end up
with a messy mess.

But don't give up! There is a simple way. You just have to edit your .py file
and explicitely tell Clustertools that you are adding new parameters. After
that you can just relaunch the experiment.

The procedure is slightly different if you want to add a brand new parameter
(e.g. change the default parameter of some method), or just a new value for
some parameter.
In the former case, you have to
  1. Adapt the computation to reflect this addition.
  2. Add a separator to the `ParameterSet` instance.
  3. Add a default value together with the separator.
  4. Add the new parameter and its value(s) after the separator.

In the case where you just want to evaluate new values of an existing parameter,
you can drop stages 1. and 3. Just add the separator and then the new values

Do `python 001_basic_usage.py front-end`. Since the experiment `BasicUsage` has
already run, you cannot adapt it directly. Now imagine that you modified
`001_basic_usage.py` as this file and run it.

Note that you can use the :meth:`add_separator` method a the `ParameterSet` to
influence the ordering the computation. But there is a dedicated way to do that
(see `006_priority.py`).
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

    experiment = Experiment("BasicUsage", param_set, MyComputation)
    environment.run(experiment)

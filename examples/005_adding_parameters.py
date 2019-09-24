# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Go through `001_basic_usage.py` before running this example. We will re-use
the same computation: x*y and z+w for x in [1, 2, 3], y = 2, z = 4,
w in [5, 6] in an experiment called BasicUsage.

In example `004_adding_parameter_values.py`, we added a new parameter value.
But what if we want to add a whole new parameter? Say we add a parameter `n`
(for noise). Maybe a default value of `n` was implicitly assumed before and
we now want to measure its effect. Of course, this will affect the results
(otherwise, we wouldn't be doing it). Therefore, we will have to adapt the
`Computation` as well.

As in example `004_adding_parameter_values.py`, if we ran the original code,
we cannot simply modify the code and run it. This will lead to a mess for the
same reasons. Once again we will add a separator to enforce some coherent
ordering. However, we need to specify the default value of our new parameter,
the one that corresponds to the computations already computed.

Concretely, we must:
  1. Adapt the computation to reflect the addition of a new parameter.
  2. Add a separator to the `ParameterSet` instance.
  3. Add a default value together with the separator (this is mandatory for
     Clustertools to be able to get a coherent ordering)
  4. Add the new parameter and its value(s) after the separator.

Run `python 000_reset.py` to reset everything (we will start back from the base
example and ignore `004_adding_parameter_values.py`) and then
`python 001_basic_usage.py front-end`. Consider now that this file is the
modification of `001_basic_usage.py` and run it with
`python 005_adding_parameters.py front-end`.

Note that you cannot run `python 002_results.py` this time because it is not
the datacube will get results with the parameter `n` (the new ones) and without
(the old ones). Refer to `005_results_with_default_params.py` instead.
"""


from clustertools import Computation, CTParser, ParameterSet, \
    Experiment, set_stdout_logging


class MyComputation(Computation):
    """
    Inherit from `Computation` and redefine the `run` method as you which
    """

    # We add the `n` parameter with a default value of 0.
    def run(self, collector, x, z, w, y=2, n=0, **parameters):
        import time
        from random import randint, normalvariate

        collector["multiply"] = x * y
        # Simulate the effect of the new parameter: in this case we add
        # some gaussian noise to the computation of the sum
        collector["sum"] = z + w + normalvariate(0, n)
        time.sleep(randint(1, 10))


if __name__ == "__main__":
    set_stdout_logging()

    parser = CTParser()

    environment, _ = parser.parse()

    param_set = ParameterSet()
    param_set.add_parameters(x=[1, 2, 3], z=4, w=[5, 6])

    # Add the separator, the default value for what was computed previously and
    # the new parameter values
    # -- Separator (compare this to `004_adding_parameter_values.py`)
    param_set.add_separator(n=0)  # Notice we pass the default value
    # -- new parameter values
    param_set.add_parameters(n=[0.01, 0.001])

    experiment = Experiment("BasicUsage", param_set, MyComputation)
    environment.run(experiment)


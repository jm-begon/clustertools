# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
In this example, we will impose an ordering of the computations so that some
parameter get computed before other.
To do so, we will adapt the `001_basic_usage.py` example.

Concretely, we will impose that the computations for x=3 be done in priority.
One could also impose a priority for other parameters or event for another value
of the same parameters.

:cls:`PrioritizedParamSet` is a decorator class for `ParameterSet`. At
creation, it takes a `ParameterSet` to whom/which it delegates all the basic
resposabilites (generating the cartesian product of the parameters, adding
separators (see `004_adding_parameter_values.py` and
`005_adding_parameters.py`), etc.). It offers the possibility to change the
ordering of the computations through its method :meth:`prioritize`.

Note one can change the priority even once some computations have already
run with another (possibly the default) priority. Isn't it nice ?

The workflow is the following:
  1. Create a :cls:`PrioritizedParamSet` that takes the regular
     :cls:`ParameterSet` at creation
  2. Use its :meth:`prioritize` method to -- ok you've guessed it

Run the following command lines:
`python 000_reset.py` to reset the 'BasicUsage' experiment
`python 007_priority.py front-end --capacity 2` to run the three firsts
    computations
See from the logging output (debug level) how the only two launched computations
are the ones with x=3.
"""

# We need to import `PrioritizedParamSet`
from clustertools import Computation, CTParser, ParameterSet, \
    Experiment, set_stdout_logging, PrioritizedParamSet


class MyComputation(Computation):
    """
    Inherit from `Computation` and redefine the `run` method as you which
    """

    def run(self, collector, x, z, w, y=2, **parameters):
        import time
        from random import randint

        collector["multiply"] = x * y
        collector["sum"] = z + w
        time.sleep(randint(1, 10))


if __name__ == "__main__":
    set_stdout_logging()

    parser = CTParser()

    environment, _ = parser.parse()

    param_set = ParameterSet()
    param_set.add_parameters(x=[1, 2, 3], z=4, w=[5, 6])

    # We decorate our `ParameterSet` to be able to add some priorities
    param_set = PrioritizedParamSet(param_set)
    # We add the priority. The method is expecting the name of the parameter
    # and the domain value to prioritize
    param_set.prioritize('x', 3)
    # It is possible to give the next priority to another paramter:
    # param_set.prioritize('w', 5)
    # Or to give the next priority to another value of the same parameter:
    # param_set.prioritize('x', 2)

    experiment = Experiment('BasicUsage', param_set, MyComputation)
    environment.run(experiment)

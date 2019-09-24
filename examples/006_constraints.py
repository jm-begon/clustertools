# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
In this example, we will add some constraints to the combination of parameters.
To do so, we will adapt the `001_basic_usage.py` example.

:cls:`ConstrainedParameterSet` is a decorator class for ParameterSet. At
creation, it takes a `ParameterSet` to whom/which it delegates all the basic
resposabilites (generating the cartesian product of the parameters, adding
separators (see `004_adding_parameter_values.py` and
`005_adding_parameters.py`), etc.). It offers the possibility to add constraints
throught its method :meth:`add_constraints`.

The workflow is the following:
  1. Define a filtering function which takes all the parameters
  2. Create a :cls:`ConstrainedParameterSet` that takes the regular
     :cls:`ParameterSet` at creation
  3. Add the filtering function to the :cls:`ConstrainedParameterSet`

Needless to say that the resulting datacube will not be complete.

Run the following command lines:
`python 000_reset.py` to reset the 'BasicUsage' experiment
`python 006_constraints.py front-end` to run the experiment with constraints
`python 002_results.py` to see the difference with the vanilla experiment
"""

# We need to import `ConstrainedParameterSet`
from clustertools import Computation, CTParser, ParameterSet, \
    Experiment, set_stdout_logging, ConstrainedParameterSet


# We define a filtering function which will be used to filter out some
# computations.
# Since it will get all the parameter but we only care about x and w,
# we can absorb the rest in the kwargs.
# The name does not have to be as crude as the one that is used here.
def not_x_eq_3_and_w_eq_6(x, w, **kwargs):
    # The predicate will only prevent the case where x=3 and w=6, in all other
    # cases, it will return True
    if x == 3 and w == 6:
        return False
    return True


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

    # We decorate our `ParameterSet` to be able to prevent some computations
    param_set = ConstrainedParameterSet(param_set)
    # We add the constrain
    param_set.add_constraints(not_x3_and_w6=not_x_eq_3_and_w_eq_6)

    experiment = Experiment('BasicUsage', param_set, MyComputation)
    environment.run(experiment)

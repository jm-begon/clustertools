# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Sometimes, a computation needs some information from the user which are not
strictly speaking parameters of the computation (in the sense that they
do not influence the result). Moreover, it might so happen that these parameters
vary. This the case when
 - Needing to access some file which are at different places on different
   machines, while keeping the code as acgnostic as possible
 - Specifying different resources needed by the job, and using that information
   in the code (e.g. requiring several CPUs and using that number to spawn
   a pool)

We will refer to these as environment parameters. Using those as inputs of the
`run` method of a computation (possibly via a `ParameterSet`) will result
in an erroneous datacube: the environment parameters will appear as several
computation parameters, and the resulting cube will not be considered complete.

The solution is to give these values at the constructor of the `Computation`
subclass and to change the factory given to the `Experiment` constructor.
To do that, we will use the `partial` function.

The code is based on `001_basic_usage.py`, so if you are unclear, start there.
"""

from clustertools import Computation, CTParser, ParameterSet, \
    Experiment, set_stdout_logging


class MyComputation(Computation):
    def __init__(self, my_environment_parameter, exp_name, comp_name,
                 context, storage_factory):
        # We re-implement the constructor to be able to store our environment
        # parameter
        super().__init__(exp_name, comp_name, context, storage_factory)
        self.my_environment_parameter = my_environment_parameter

    def run(self, collector, x, z, w, y=2, **parameters):
        import time
        from random import randint

        # We can access our environment parameter
        print(self.my_environment_parameter)

        collector["multiply"] = x * y
        collector["sum"] = z + w
        time.sleep(randint(1, 10))


if __name__ == "__main__":
    set_stdout_logging()
    parser = CTParser()
    environment, _ = parser.parse()

    param_set = ParameterSet()
    param_set.add_parameters(x=[1, 2, 3], z=4, w=[5, 6])

    # We use the :meth:`partialize` class method to specialize the
    # computation class with our environment parameter
    my_factory = MyComputation.partialize(my_environment_parameter="Test")

    experiment = Experiment("BasicUsage", param_set, my_factory)

    environment.run(experiment)

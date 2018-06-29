# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
This minimum working example illustrate the use of `Clustertools` to run
a simple experiment. The (dummy) experiment consist in computing the
multiplication and addition of several numbers. More specifically, we will
compute x*y and z+w for x in [1, 2, 3], y = 2, z = 4, w in [5, 6].

The computation will be done in the current process, purely sequentially.
"""


from clustertools import Computation, ParameterSet, InSituEnvironment, \
    Experiment, set_stdout_logging


class BasicComputation(Computation):
    """
    Inherit from `Computation` and redefine the `run` method as you which
    """

    def run(self, result, x, z, w, y=2, **parameters):
        # For dill, import must be in the scope of the serialized object
        import time
        from random import randint

        # Do some heavy number crunching
        result["multiply"] = x * y
        result["sum"] = z + w
        time.sleep(randint(1, 10))
        print("HARRY POTTER !")

        # Result is automatically collected.
        # Everything (saving, updating status, etc.) is taken care of


if __name__ == "__main__":
    # Configure logging to debug on stdout
    set_stdout_logging()

    # Create environment
    environment = InSituEnvironment(stdout=True)

    # Define the parameter set: the domain each variable can take
    param_set = ParameterSet()
    param_set.add_parameters(x=[1, 2, 3], z=4, w=[5, 6])

    # Wrap it together as an experiment
    experiment = Experiment("InSitu", param_set, BasicComputation)

    # Finally run the experiment
    environment.run(experiment)






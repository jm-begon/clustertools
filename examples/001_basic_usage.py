# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
This minimum working example illustrate the use of `Clustertools` to run
a simple experiment. The (dummy) experiment consist in computing the
multiplication and addition of several numbers. More specifically, we will
compute x*y and z+w for x in [1, 2, 3], y = 2, z = 4, w in [5, 6].

To test the code, do `python 001_basic_usage.py front-end`.

You can choose an other backend than `front-end` It must be one of:
debug, front-end, bash, slurm.

Note that you might not be able to use some backend. For instance, Slurm might
not be installed. Use `python 001_basic_usage.py -h` to see the help. There is
also some help and specific parameters for each back end. Check them out with
`python 001_basic_usage.py <backend> -h`

Enjoy!
"""


from clustertools import Computation, CTParser, ParameterSet, \
    Experiment, set_stdout_logging


class MyComputation(Computation):
    """
    Inherit from `Computation` and redefine the `run` method as you which
    """

    def run(self, collector, x, z, w, y=2, **parameters):
        # For encapsulation reasons, all imports needed for the computation
        # must be in the scope of the serialized object
        import time
        from random import randint

        # Do some heavy number crunching
        collector["multiply"] = x * y
        collector["sum"] = z + w
        time.sleep(randint(1, 10))

        # Result is automatically collected.
        # Everything (saving, updating status, etc.) is taken care of


if __name__ == "__main__":
    # Configure logging to debug on stdout (the verbosity level can be adapted)
    set_stdout_logging()

    # Create the command line parser. It allows you to specify the backend,
    # as well as parameters related to the backend
    parser = CTParser()

    # Read from the command line and create an `Environment` to run the code
    # into
    environment, _ = parser.parse()

    # Define the parameter set: the domain each variable can take
    param_set = ParameterSet()
    param_set.add_parameters(x=[1, 2, 3], z=4, w=[5, 6])

    # Wrap it together as an experiment
    experiment = Experiment("BasicUsage", param_set, MyComputation)

    # Finally run the experiment
    environment.run(experiment)

    # You can now head to `002_results.py`

# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
This minimum working example illustrate the use of `Clustertools` to run
a simple experiment. The (dummy) experiment consist in computing the
multiplication and addition of several numbers. More specifically, we will
compute x*y and z+w for x in [1, 2, 3], y = 2, z = 4, w in [5, 6].

The computation will be done in bash directly. If you want to run the
same piece of code on a Slurm cluster, see file `basic_cluster.py`
"""


from clustertools import Computation, BaseParser, ParameterSet, \
    Experiment, Serializer, set_stdout_logging


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
        # Result is automatically collected.
        # Everything (saving, updating status, etc.) is taken care of



if __name__ == "__main__":
    # Configure logging to debug on stdout
    set_stdout_logging()

    # Create the parser
    parser = BaseParser(Serializer)

    # Read from the command line and create an `Environment` to run the code
    # into
    environment, _ = parser.parse()

    # Define the parameter set: the domain each variable can take
    param_set = ParameterSet()
    param_set.add_parameters(x=[1, 2, 3], z=4, w=[5, 6])

    # Wrap it together as an experiment
    experiment = Experiment("BasicBash", param_set, BasicComputation)

    # Finally run the experiment
    environment.run(experiment)






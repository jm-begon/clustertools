# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
In this example, we will add custom command line parameters. It re-uses the
example of `001_basic_usage.py` so if you are unclear, start there.

Adding command line parameters is helpful when we want to re-use the same
`Computation` class and only one file for different settings but generate
different experiments. A common case is when working with several datasets:
they may not need the same resources or you might want to distinguish them by
their name up front.

In this example, we will illustrate how to do that by changing the value of
the parameter `y` from the command line. Changes to `001_basic_usage.py` are
minimal:
  1. add an argument to the parser
  2. use it in the parameter set
  3. rename the experiment according to this parameter
and voila

Run this experiment with the following command lines:
`python 0003_custom_arguments.py front-end --y 1`
`python 0003_custom_arguments.py front-end --y 3`
`python 0003_custom_arguments.py front-end --y 1`

You should see that the two firsts trigger the computation whereas the last one
doesn't
"""


from clustertools import Computation, CTParser, ParameterSet, \
    Experiment, set_stdout_logging


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

    # Add custom argument to parser
    parser.add_argument("y", help="The value of the `y` parameter", type=int)

    environment, namespace = parser.parse()

    param_set = ParameterSet()
    # add `y` given in command line to parameter set
    param_set.add_parameters(x=[1, 2, 3], z=4, w=[5, 6], y=namespace.y)

    # Change the name of the computation according to the value of `y`
    # Note that this is mandatory. Otherwise, Clustertools cannot distinguish
    # between the two "sub" experiment
    exp_name = "BasicUsage_{}".format(namespace.y)
    print("This is experiment", exp_name)
    experiment = Experiment(exp_name, param_set, MyComputation)

    environment.run(experiment)

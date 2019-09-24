# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
This example illustrates how the computation can notify of advancing progress:
it simply uses the :meth:`notify_progress` method. This method expects a real
number between 0 and 1, 1 meaning 100% completion.

Monitoring progress is best done with the Clustertools utility `clustertools`.
Prepare two terminals. In the first one, run this experiment with
`python 008_monitoring_progress.py front-end`. In the second one do
`clustertools count BasicUsageMonitoring` several times. You should see the
progress evolves.

Instead of using the `clustertools` utility, you enter a python console and
use the :cls:`Monitor` class to track your computations.
"""


from clustertools import Computation, CTParser, ParameterSet, \
    Experiment, set_stdout_logging


class MyComputation(Computation):
    """
    Inherit from `Computation` and redefine the `run` method as you which.

    This computation will perform 100 steps of the bisection method to find a
    root for x^3 - x - 2 on [a, b]
    """

    def run(self, collector, a, b, **parameters):
        import time

        # The polynome for which we are trying to find the roots
        def P(x):
            return x**3 - x - 2

        # Bisection algorithm
        m = 0
        for i in range(100):
            m = (a+b)/2.
            if P(a)*P(m) < 0:
                b = m
            else:
                a = m

            # Notify the progression of the task. `notify_progress` takes as
            # input a float between 0 and 1
            self.notify_progress((i+1)/100.)

            # Wait some time to be able to see the update with
            # `clustertools count`
            time.sleep(1)

        collector["root"] = m


if __name__ == "__main__":
    set_stdout_logging()

    parser = CTParser()

    environment, _ = parser.parse()

    param_set = ParameterSet()
    param_set.add_parameters(a=1, b=2)

    experiment = Experiment("BasicUsageMonitoring", param_set, MyComputation)
    environment.run(experiment)

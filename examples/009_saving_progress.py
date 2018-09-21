# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Clustertools offers the possibility to save partial results. This is handy with
long computations that can get interrupted (by a job scheduler like Slurm for
instance).

You just need to use the :meth:`save_result` method from the `Computation`
class.

So far, there is no way to restart a interrupted computation from the last save
point. Pull requests are welcome(d)

To run this example, open two terminals. In the first one, run this example
(`python 009_saving_progress.py front-end`). In the second, do
`python 009_partial_results.py`. Every few seconds, you should see advances
in the root precision
"""


from clustertools import Computation, CTParser, ParameterSet, \
    Experiment, set_stdout_logging


class MyComputation(Computation):
    """
    Inherit from `Computation` and redefine the `run` method as you which.

    This computation will perform steps of the bisection method to find a
    root for x^3 - x - 2 on [a, b] up to a precision of 1e-50 (which should
    take around 50 iterations)
    """

    def run(self, result, a, b, **parameters):
        import time

        # The polynome for which we are trying to find the roots
        def P(x):
            return x**3 - x - 2

        # Bisection algorithm
        m = i = 0
        while abs(a-b) >= 1e-50:
            m = (a+b)/2.
            if P(a)*P(m) < 0:
                b = m
            else:
                a = m

            # Update result at each iteration. Saving the iteration number is
            # just there for nicer formatting on the result side
            result["root"] = m
            result["iteration"] = i

            if i % 10 == 0:
                # Saving the result every 10 iterations
                self.save_result()

            # Wait some time to be able to see the update when running
            # `python 009_partial_results.py`
            time.sleep(1)
            i += 1


if __name__ == "__main__":
    set_stdout_logging()

    parser = CTParser()

    environment, _ = parser.parse()

    param_set = ParameterSet()
    param_set.add_parameters(a=1, b=2)

    experiment = Experiment("BasicUsagePartialSave", param_set, MyComputation)
    environment.run(experiment)

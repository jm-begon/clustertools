# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Go through `001_basic_usage.py` before running this example.

If you did so, you computed the x*y and z+w
for x in [1, 2, 3], y = 2, z = 4, w in [5, 6] in a experiment called
`BasicUsage`. Under the hood, Clustertools generated the individual
computations, managed their states and logging and saved the results.

We are now ready to load all the results and analyze them. Clustertools provides
a `Datacube` class, easily built throught the function `build_datacube` which
expects the name of the experiment.

`Datacube` is built around two main concepts. On the one hand, we have the
inputs of the computations, which are called variables. On the other, we have
the results, which are called -- drum roll -- results.

We can further distinguish between two types of variables. When a variable has
the same value throughout the whole experiment, it is a constant or as we call
it, a metadata. If it is not a metadata, it is a paremeter. The different values
it can take form the domain of that parameter.
"""
import sys

from clustertools import build_datacube

if __name__ == '__main__':
    # Load the data of experiment `BasicUsage` (from `001_basic_usage.py`) and
    # create a datacube with it.
    cube = build_datacube("BasicUsage")
    if len(cube) == 0:
        print("Results of experiment 'BasicUsage' not found.")
        sys.exit(1)

    # First we can look at the repr of the cube to see the parameters, their
    # domains and the metadata
    print("Representation of the cube:\n", repr(cube), "\n")

    # We can make a diagnosis of the cube to see if some data is missing
    print("Diagnose:\n", cube.diagnose(), "\n")

    print()
    print("---------------------------- INDEXING ----------------------------")
    # `Datacube` is a callable, which accepts an optional metric name and
    # pairs of parameter name-parameter value. This is the preferred access way
    print("Value of 'sum' for x=1 and w=5", cube("sum", x='1', w='5'), "\n")
    # Notice how the actual values are string. This is a constraint enforced
    # to ensure a consistent use (domain values could be string)

    print()
    print("------------------------- SLICING & DICING ------------------------")
    # Slicing and dicing are most usually done through application call as well

    # 1. Dicing (i.e. picking up a subdomain for one or more variable)
    print("Dicing of x to [1, 2]:", repr(cube(x=['1', '2'])), "\n")

    # 2. Slicing (i.e. removing one variable by fixing its values)
    print("Slicing of x at 1:", repr(cube(x='1')))
    print("   Notice how x has become a metadata.\n")

    print()
    print("------------------- SLICING, DICING, INDEXING ---------------------")
    # As long as there is one variable which is not set or there is more than
    # one metric, the application call will return a new `Datacube` object.
    # If this is not the case, the base object is returned like an indexing.
    cube_x_1 = cube(x='1')
    print("First slicing (x=1):", repr(cube_x_1), "\n")
    cube_x_1_sum = cube_x_1("sum")
    print("Then selecting only 'sum' metric:", repr(cube_x_1_sum), "\n")
    print("Then slicing again (w=5)", repr(cube_x_1_sum(w='5')), "\n")
    # When slicing or dicing, a new view is created but the underlying buffer
    # is shared (anyway, since they are results of experiment, they are not
    # meant to be tempered with)

    print()
    print("------------------- ITERATING THROUGH THE CUBE --------------------")
    # In order to plot results, one usually needs to iterate through the
    # datacube. Although this can be achieve with slicing/dicing/indexing
    # operations, it feels cumbersome for something so frequent. Therefore,
    # one can use the :meth:`iter_dimensions` method
    print("Iterating over x:")
    for t_x, cube_i in cube.iter_dimensions("x"):
        print(t_x, repr(cube_i))
    # Notice how x is a tuple

    print("\n", "Iterating over x and w and printing 'mult'"
                " (=x*y, not x*w):")
    for t, cube_i in cube.iter_dimensions("x", "w"):
        print(t, cube_i("multiply"))

    print()
    # -------------------------- ROLL UP/DRILL DOWN -------------------------- #
    # Coming soon (implementation not there yet). However, when the metric
    # is numeric, is it easy to cast the datacube as NumPy array with the
    # :meth:`numpyfy` method.
    # NumPy arrays have a built-in support for those kind of operations
    try:
        import numpy as np
        np_array = cube("sum", x='1').numpyfy()
        print("Sum for x=1 as array:", np_array, "\n")
        print("Mean of it", np_array.mean())
    except ImportError:
        print("Install NumPy for external roll up.")

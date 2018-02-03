# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
This minimum working examples illustrate the use of `Clustertools` `Datacube`.
You should have run the `basic_bash.py` example BEFOREHAND, otherwise there will
be no data to analyze.

The experiment consisted in computing the multiplication and addition of
several numbers. More specifically, we will compute x*y and z+w
for x in [1, 2, 3], y = 2, z = 4, w in [5, 6].
"""
import sys

from clustertools import build_datacube

if __name__ == '__main__':
    # Load the data of experiment `BasicBash` (from `basic_bash.py`) and
    # create a datacube with it.
    cube = build_datacube("BasicBash")
    if len(cube) == 0:
        print("Results of experiment 'BasicBash' not found.")
        sys.exit(1)

    # First we can look at the repr of the cube to see the variables, their
    # domains and the metaparameters
    print("Representation of the cube:\n", repr(cube), "\n")

    # We can make a diagnosis of the cube to see if there is missing data
    print("Diagnose:\n", cube.diagnose(), "\n")

    print()
    print("---------------------------- INDEXING ----------------------------")
    # The preferred way to access is through the application call where we
    # can named both the variables and metrics
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
    # one metric, the application call will return a new cube object. If this
    # is not the case, the base object is returned like an indexing.
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
    # Coming soon (implementation not there yet)
    try:
        import numpy as np
        np_array = cube("sum", x='1').numpyfy()
        print("Sum for x=1 as array:", np_array, "\n")
        print("Mean of it", np_array.mean())
    except ImportError:
        print("Install NumPy for external roll up.")

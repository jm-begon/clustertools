# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
This result example is dedicated to the script `005_adding_parameters.py`. Make
sure you have run that one before proceeding.

In this example, we will see how to handle the addition of new parameters when
working with the datacube. The datacube cannot handle it because parts of the
results were saved without an explicit value for the missing parameter.
Therefore, when the `build_datacube` function sees some results with the new
parameter, it does not know what to do of it.

For this, there is an easy solution: the
`build_datacube` function accepts key-based optional parameters where the key
is the name of the parameter and the value is its default value.
"""
import sys

from clustertools import build_datacube

if __name__ == '__main__':

    # Compare to `002_results.py`, we simply add the n=0 kwarg to tell the
    # function to use this default value when `n` is missing. We can of course
    # have more than one such default values
    cube = build_datacube('BasicUsage', n=0)
    if len(cube) == 0:
        print("Results of experiment 'BasicUsage' not found.")
        sys.exit(1)

    # Notice how `n` has become a parameter and has a domain
    print("Representation of the cube:\n", repr(cube), "\n")

    # We can iterate over the new parameter, and do all we could do with regular
    # parameters
    for t, cube_i in cube.iter_dimensions('n'):
        print('n =', t, '/', cube_i.domain)


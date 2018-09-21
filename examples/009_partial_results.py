# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
This result example is dedicated to the script `009_saving_progress.py`. Make
sure you are running that one simultaneously.

There is nothing to learn from this example. It is just there to show the effect
of partial saving
"""
import time

from clustertools import build_datacube

if __name__ == '__main__':
    exp_name = 'BasicUsagePartialSave'

    mask = "{:15} {:15}"
    print(mask.format("Iter. #", "Root value"))

    for _ in range(100):
        cube = build_datacube(exp_name)
        if len(cube) == 0:
            print(mask.format('n/a', 'n/a'))
        else:
            it_num, root_val = cube('iteration'), cube('root')
            print(mask.format(it_num, root_val))
            if it_num % 10 != 0:
                break
        time.sleep(5)



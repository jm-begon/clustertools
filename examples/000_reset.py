# -*- coding: utf-8 -*-
#!/usr/bin/env python

import argparse

from clustertools import Architecture
from clustertools import set_stdout_logging


__DOC__ = """
This script is only here to reset the experiments that are used in the context
of Clustertools examples. Use it to restore the setting as if none of the
examples had been run.

Do not use it if you have experiments whose name starts with 'BasicUsage' (but
do not use that name for your experiments, choose more descriptive ones).

WARNING: the method used in this script will removed definitively the
experiment (all the results, logs, states, etc.) If you want to explicitly
change the state of some computation (e.g. change some aborted to jobs to be
able to launch them again was the error is solved) or reset in a softer way
(mark computations has launchable but keep the logs and the results -- as long
as they are not overridden by relaunching the experiment) the whole experiment,
check out the `clustertools` command line utility which is shipped with
Clustertools.
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__DOC__,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--debug', default=False, action='store_true',
                        help='list what would be erased instead '
                             'of doing it')

    args = parser.parse_args()

    # Configure logging to debug on stdout (the verbosity level can be adapted)
    set_stdout_logging()

    # :cls:`Architecture` is responsible for managing the folders where
    # everything related to Clustertools is stored
    architecture = Architecture()

    # Get all experiment names
    for exp_name in architecture.load_experiment_names():
        if exp_name.startswith('BasicUsage'):
            if args.debug:
                print(exp_name)
            else:
                # Actually erase the whole experiment
                # WARNING: this cannot be undone!
                architecture.erase_experiment(exp_name)

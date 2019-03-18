#!/bin/bash
# This script is meant to be called by the "install" step defined in
# .travis.yml. See http://docs.travis-ci.com/ for more details.
# The behavior of the script is controlled by environment variabled defined
# in the .travis.yml in the top level folder of the project.

# License: 3-clause BSD


set -xe # Exit on first error


if [[ "$SCHEDULER" == "SLURM" ]]; then
    apt-cache search slurm-llnl
    sudo apt-get install slurm-llnl
    sudo apt-get install munge
    sudo /usr/sbin/create-munge-key
    sudo service munge start
    sudo python continuous_integration/configure_slurm.py
fi
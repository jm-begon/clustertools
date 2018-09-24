ClusterTools
============

[![Build Status](https://travis-ci.org/jm-begon/clustertools.svg?branch=master)](https://travis-ci.org/jm-begon/clustertools)
[![Coverage Status](https://coveralls.io/repos/github/jm-begon/clustertools/badge.svg)](https://coveralls.io/github/jm-begon/clustertools)

ClusterTools is a toolkit to run experiments on supercomputers.

 * You need to run a given experiment with many different sets of parameters?
 * You don't fancy writing many files?
 * You'd rather not go through many lines of text to monitor the progress
 of your computations?
 * You find that saving the results are messy?
 * ... and analyzing them is so much worse?
 * You are tired of crawling your own directories?
 * ... and of forgetting what you have done before?
 * ... and of changing all the scripts when you want to play with a new 
 parameter?
 
 
Stop where you are, 'cause you are there!

Clustertools offers "1 file experiment" environment, managing easily the
(cartesian product) of the parameters, tracking the state of your tasks, saving
results and logs and helping greatly with the analysis in a OLAP fashion.

Learn more about clustertools on the 
[wiki](https://github.com/jm-begon/clustertools/wiki)

If you need something more lightweight, consider using 
[!][clusterlib] (https://github.com/clusterlib/clusterlib).

Dependencies
------------
The following dependencies are necessary to use the toolkit

 * dill >= 0.2.7.1
 
In order to test the code, there is an additional need for

 * nose >= 1.3.7
 * coverage >= 4.4.2
 
If you plan to use the `Datacube` class to analyze the results, you will also need

 * numpy >= 1.11.1
 
You may use `pip install -r requirements.txt` to install all requirements.

Clustertools comes with a command-line app named `clustertools`. This app can 
query remotely the computer on which your code is running. It relies on 
`ssh` and `rsync` unix programs. These are optional components and the 
main toolkit runs on Windows environment seamlessly (as far as I am aware at 
least).

Install
-------

### With git
clone this repository and use

    python setup.py install
    
Clustertools howto
--------
Want to know more about Clustertools? See the [wiki](https://github.com/jm-begon/clustertools/wiki). 

Environments
------------
So far, only Slurm (https://slurm.schedmd.com/) is covered as super-computer backend.
SGE (http://gridscheduler.sourceforge.net/) could be covered with minimal effort 

License
-------
[BSD 3](https://github.com/jm-begon/clustertools/blob/master/LICENSE)


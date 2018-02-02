ClusterTools
============
ClusterTools is a toolkit to run experiments on supercomputers. It is built on 
top of clusterlib (https://github.com/clusterlib/clusterlib).

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
results and logs and helping greatly with the analyzis in a OLAP fashion.

Dependencies
------------
The following dependencies are necessary to use the toolkit

 * clusterlib >= 0.2.0
 * dill >= 0.2.7.1
 
In order to test the code, there is an additional need for

 * nose >= 1.3.7
 * coverage >= 4.4.2
 
If you plan to use the `Datacube`class to analyze the results, you will also need

 * numpy >= 1.11.1
 
You may use `pip install -r requirements.txt` to install all requirements.
 
As for the app suite (`ct_count`, `ct_display`, `ct_remote`, `ct_sync`) they 
rely on `ssh` and `rsync` programs. These are optional components and the 
main toolkit runs on Windows environment seamlessly (as far as I am aware at 
least).

Install
-------

### With git
clone this repository and use

    python setup.py install
    
Examples
--------
The examples folder contains a couple of scripts demonstrating the use of 
`Clustertools`

Environment
-----------
So far, only Slurm (https://slurm.schedmd.com/) is covered. 
SGE (http://gridscheduler.sourceforge.net/) could be covered with minimal effort 




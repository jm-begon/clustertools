TODOs
=====
- [x] Reset pending jobs
- [x] Partial saving + partial status
- [x] Remote survey
- [x] Add after in Experiment
- [x] Sync
- [ ] Partial reloading
- [ ] Remote launching
- [x] Refactoring
- [ ] Refactoring 2
- [ ] Result class for Computation (cf. Refactoring 2)
- [ ] Delayed launcher and 1 file per experiment
- [ ] Roll up (aggregation over one dimension)
- [ ] Drill down/up (hierarchical scaling: aggregating and changing the dimension name, scale, values, etc.)
- [ ] Automatic resource management & job relaunch

Result class
------------
- [ ] Deal with floats and stuff as such

Automatic resource management & job relaunch
--------------------------------------------
Either use contrab or manual relaunch but with automatic resource managment

Refactoring
-----------
- [ ] Scheduler
- [ ] Storage

Scheduler takes the Experiment class and manages the computations (slurm/SGE via clusterlib, joblib, direct batch).

Storage is responsible for storing notifications and results from computations.

Quid of the experiment DB ?

Refactoring 2
-------------
 - [ ] Restult -> Datacube
 - [ ] notification module -> status module
 - [ ] Historic -> Monitor

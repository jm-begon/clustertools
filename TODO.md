TODO
====
- [x] Reset pending jobs
- [x] Partial saving + partial status
- [ ] Result class
- [ ] Add after in Experiment
- [ ] Remote launching
- [ ] Refactoring
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


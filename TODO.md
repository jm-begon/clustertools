TODOs
=====
- [x] Reset pending jobs
- [x] Partial saving + partial status
- [x] Remote survey
- [x] Add after in Experiment
- [ ] pkl files to sqlite3 ?
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


Changelog
=========

New in verison 0.1.3
--------------------
 - Three new sub-pograms in the `clustertools` program
   - `version` prints the version of Clustertools
   - `launchable` makes a single `Computation` launchable
   - `diagnose` loads a datacube and prints its diagnosis
 - `InSituEnvironment` will refresh automatically before launching a new 
 computation
 - More context information have been added (timestamp and hostname)
 - A few fixes
 - Refactoring of the `ParameterSet` hierachy
 - Multi-type parameter values (Thanks to @Waliens)

New in version 0.1.2
--------------------
 - Finally added test for Slurm
 - Creation of `CTParser` class to choose environment/backend from command line
 - Creation of `clustertools` utility to
 - Ability to notify the progression of a task and to save partial results
 - Refactoring of the `ParameterSet` classes (aka decorator are awesome)
 - Better state management in case of interruption
 - Support for GPU (not exhaustively tested)
 - Learn by example approach
 - Drop `clusterlib` requirements
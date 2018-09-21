Examples
========
The example files depict some features of Clustertools.
 
The file `000_reset.py` reset the `BasicUsage` pseudo-experiments use throughout 
the examples.

The `001_basic_usage.py`, `003_custom_arguments.py`, 
`004_adding_parameter_values.py`, `005_adding_parameters.py`, 
`006_constraints.py`, `007_priority.py`, `008_monitoring_progress.py`,
`009_saving_progress.py` and `010_logs_and_prints.py` scripts illustrate some
features of Clustertools. They rely on the `CTParser` class which provides a
standard parser. It requires the environment/backend to be specified and accepts
additional parameters. See `001_basic_usage.py` for more information or the 
parser help: `python 001_basic_usage.py -h`. You can also learn more about the
`CTParser` on the 
[wiki](https://github.com/jm-begon/clustertools/wiki/Core-concepts#parser)


The `002_result.py`, `005_results_with_default_params.py` and 
`009_partial_results.py` can be launched directly with `python <script>`. 

In all files, a header provide information about how to run the scripts and also
information to help you master Clustertools. The examples are also heavily
commented on the specific features they present.

For yet more information and howtos see the [wiki](https://github.com/jm-begon/clustertools/wiki)

Lost? Start by `001_basic_usage.py`.
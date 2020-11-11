#!/usr/bin/env python
from clustertools import Experiment

from clustertools import PythonScriptComputation, ParameterSet, \
    FileSerializer, set_stdout_logging
from clustertools.parser import CTParser



if __name__ == '__main__':
    import os
    import importlib

    set_stdout_logging()
    exp_name = PythonScriptComputation.__name__

    parser = CTParser(FileSerializer, exp_name)

    parser.add_argument("experiment_name")
    parser.add_argument("script_path")
    parser.add_argument("kwargs", nargs="*", help="kwargs argument for the "
                                                  "script. use a `key=value` "
                                                  "syntax.")

    environment, args = parser.parse()

    exp_name = args.experiment_name
    script_path = os.path.expanduser(args.script_path)

    param_set = ParameterSet()
    path = os.path.abspath(args.script_path)
    param_set.add_parameters(script_path=path)
    for t in args.kwargs:
        key, value = t.replace("--", "").split("=")
        param_set.add_parameters(key=value)

    # Loading the main function
    mod_name = os.path.basename(script_path)[:-3]  # removing .py
    mod_spec = importlib.util.spec_from_file_location(mod_name, script_path)
    module = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(module)
    main_fn = module.main


    experiment = Experiment(exp_name, param_set,
                            PythonScriptComputation.factory(main_fn))

    environment.run(experiment)










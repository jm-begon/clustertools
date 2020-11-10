#!/usr/bin/env python

from clustertools import ScriptComputation, ParameterSet, \
    FileSerializer, set_stdout_logging
from clustertools.parser import CTParser



if __name__ == '__main__':
    import os

    set_stdout_logging()
    exp_name = ScriptComputation.__name__

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
    for t in args.kwargs:
        key, value = t.replace("--", "").split("=")
        param_set.add_parameters(key=value)










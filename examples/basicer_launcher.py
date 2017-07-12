# -*- coding: utf-8 -*-
#!/usr/bin/env python


from clustertools import ParameterSet, run_experiment, bash_submit

if __name__ == "__main__":
    experiment = ParameterSet("basicer")
    experiment.add_params(a=[4,5], b=6, z=0)
    experiment.add_params(b=[7,8])
    experiment.add_params(a=6)
    run_experiment(experiment, "basicer_exp.py", bash_submit)





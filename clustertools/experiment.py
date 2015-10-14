# -*- coding: utf-8 -*-

"""
Module :mod:`experiment` is a set of functions and classes to build, run and
monitor experiments

Restriction
-----------
Experiment names should always elligible file names.
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

import sys, os
import subprocess
from subprocess import CalledProcessError
import logging
from itertools import product

from clusterlib.scheduler import submit

from .database import save_result, save_experiment, load_results
from .notification import (pending_job_update, running_job_update,
                           completed_job_update, aborted_job_update, Historic)
from .util import encode_kwargs

__EXP_NAME__ = "Experiment"
__PARAMETERS__ = "Parameters"
__RESULTS__ = "Results"


class Computation(object):

    def __init__(self, exp_name, comp_name, overwrite=True):
        self.exp_name = exp_name
        self.comp_name = comp_name
        self.overwrite = overwrite

    def run(self, **parameters):
        pass

    def __call__(self, **parameters):
        start = running_job_update(self.exp_name, self.comp_name)
        try:
            result = {
                self.comp_name: {
                    __EXP_NAME__: self.exp_name,
                    __PARAMETERS__: parameters,
                    __RESULTS__: self.run(**parameters)
                }
            }
            save_result(self.exp_name, result)
            completed_job_update(self.exp_name, self.comp_name, start)
        except Exception as excep:
            aborted_job_update(self.exp_name, self.comp_name, start, excep)
            raise




class Experiment(object):

    def __init__(self, name, params=None):
        self.name = name
        if not params:
            self.params = {}
        else:
            self.params = params

    def add_params(self, **kwargs):
        for k, v in kwargs.iteritems():
            vp = self.params.get(k)
            if vp is None:
                vp = []
                self.params[k] = vp
            try:
                if isinstance(v, basestring):
                    raise TypeError
                for vi in v:
                    vp.append(vi)
            except TypeError:
                vp.append(v)
            finally:
                vp.sort()

    def get_metadata(self):
        d = {}
        for k, v in self.params.iteritems():
            if len(v) == 1:
                d[k] = v[0]
        return d

    def get_domain(self):
        d = {}
        for k, v in self.params.iteritems():
            if len(v) > 1:
                d[k] = v
        return d

    def __len__(self):
        nb = 1
        for val in self.params.values():
            nb *= len(val)
        return nb

    def __iter__(self):
        if len(self.params) == 0:
            yield "Computation-"+self.name+"-0", self.serialize({})
        else:
            keys = self.params.keys()
            keys.sort()
            values = [self.params[k] for k in keys]
            for i, v in enumerate(product(*values)):
                params = dict(zip(keys, v))
                label = "Computation-"+self.name+"-"+str(i)
                yield label, params

    def get_params_for(self, sel):
        index = -1
        name = ""
        try:
            index = int(sel)
            # sel is a int
            if index < 0 or index >= len(self):
                raise KeyError("%d not in the range [0, %d]" %
                                    (index, len(self)-1))
        except ValueError:
            # sel is a string
            name = sel
        for i, (label, param) in enumerate(self):
            if i == index or name.encode("utf-8") == label.encode("utf-8"):
                return label, param
        raise KeyError("Key '%s' not found" % str(sel))

    def __getitem__(self, sel):
        return self.get_params_for(sel)

    def __str__(self):
        return "Experiment '%s': %s" % (self.name, str(self.params))


def build_result_cube(exp_name):
    res = load_results(exp_name)
    parameterss = []
    resultss = []
    for d in res.values():
        parameterss.append(d[__PARAMETERS__])
        resultss.append(d[__RESULTS__])
    return Result(parameterss, resultss, exp_name)

class Result(object):
    """
    parameterss : iterable of mappings name -> value
    resultss : iterable of mappings name -> value
    """
    def __init__(self, parameterss, resultss, exp_name=""):
        param_tmp = {}
        for parameters in parameterss:
            for k, v in parameters.iteritems():
                _set = param_tmp.get(k)
                if _set is None:
                    _set = set()
                    param_tmp[k] = _set
                _set.add(v)
        print param_tmp
        metadata = {}
        parameter_list = []
        domain = {}
        for k, v in param_tmp.iteritems():
            ls = [vi for vi in v]
            if len(ls) > 1:
                ls.sort()
                domain[k] = ls
                parameter_list.append(k)
            else:
                metadata[k] = ls[0]
        parameter_list.sort()

        self.name = exp_name
        self.metadata = metadata
        self.domain = domain
        self.parameters = parameter_list






def yield_not_done_computation(experiment, user=os.environ["USER"]):
    historic = Historic(experiment.name, user)
    for comp_name, param in experiment:
        if historic.is_launchable(comp_name):
            yield comp_name, param



def run_experiment(experiment, script_path, build_script=submit,
                   overwrite=True, user=os.environ["USER"],
                   serialize=encode_kwargs):
    logger = logging.getLogger("clustertools")
    exp_name = experiment.name

    save_experiment(experiment, overwrite)

    i = -1
    for job_name, param in yield_not_done_computation(experiment, user):
        i += 1
        job_command = '%s %s "%s" "%s" "%s"' % (sys.executable, script_path,
                                               exp_name, job_name,
                                               serialize(param))

        script = build_script(job_command, job_name=job_name)
        logger.debug("Script:\n%s" % script)

        start = pending_job_update(exp_name, job_name)
        try:
            output = subprocess.check_output(script, shell=True)
            logger.debug("Output:\n%s" % output)
        except CalledProcessError as exception:
            aborted_job_update(exp_name, job_name, start, exception)
            logger.error("Error launching job '%s': %s" % (job_name,
                exception.message), exc_info=True)

    logger.info("Experiment '%s': %d computation(s)" % (exp_name, (i+1)))


# -*- coding: utf-8 -*-

"""
Module :mod:`experiment` is a set of functions and classes to build, run and
monitor experiments
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

import sys
import subprocess
from subprocess import CalledProcessError
import logging
from itertools import product

from clusterlib.scheduler import submit

from .database import save_result, save_experiment
from .notification import (pending_job_update, running_job_update,
                           completed_job_update, aborted_job_update, Historic)
from .util import encode_kwargs




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
                    "Experiment": self.exp_name,
                    "Parameters": parameters,
                    "Results": self.run(**parameters)
                }
            }
            save_result(self.exp_name, result)
            completed_job_update(self.exp_name, self.comp_name, start)
        except Exception as excep:
            aborted_job_update(self.exp_name, self.comp_name, start, excep)
            raise





class Experiment(object):

    def __init__(self, name, params={}, serializer=encode_kwargs):
        self.name = name
        self.params = params
        self.serialize = serializer

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
            keys, values = zip(*self.params.items())
            for i, v in enumerate(product(*values)):
                params = dict(zip(keys, v))
                label = "Computation-"+self.name+"-"+str(i)
                yield label, self.serialize(params)




def run_experiment(experiment, script_path, build_script=submit,
                   overwrite=True):
    logger = logging.getLogger("clustertools")
    exp_name = experiment.name

    save_experiment(experiment, overwrite)


    do_not_launch = set()
    try:
        # Job notified as done in notif DB
        # --> Should be the same as previous done_jobs
        historic = Historic(exp_name)
        done_jobs = historic.already_up()
        do_not_launch.union(done_jobs)
    except Exception, reason:
        logger.warn("Trouble connecting to notification database: %s" % reason)


    for i, (job_name, param) in enumerate(experiment):
        job_command = '%s %s "%s" "%s" "%s"' % (sys.executable, script_path,
                                               exp_name, job_name, param)


        if job_name not in do_not_launch:
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

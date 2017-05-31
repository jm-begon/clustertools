# -*- coding: utf-8 -*-

"""
"""
import getpass

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

import sys, os
import subprocess
from subprocess import CalledProcessError
import logging

from clusterlib.scheduler import submit

from .notification import (pending_job_update, aborted_job_update,
                           yield_not_done_computation)
from .database import get_storage
from .util import encode_kwargs


def picklify(cpe):
    return PickableCalledProcessError(cpe.cmd, cpe.returncode, cpe.output)

class PickableCalledProcessError(CalledProcessError):
    def __init__(self, cmd="", returncode=0, output=""):
        super(PickableCalledProcessError, self).__init__(returncode, cmd, output)


def run_experiment(experiment, script_path, build_script=submit,
                   force=False, user=None,
                   serialize=encode_kwargs, capacity=sys.maxsize,
                   start=0):
    if user is None:
        user = getpass.getuser()
    exp_name = experiment.name
    logger = logging.getLogger("clustertools")
    logger.info("Launching experiment '%s' with script '%s'" %(experiment, script_path))

    get_storage(exp_name).init()

    i = 0
    for j, (job_name, param) in enumerate(yield_not_done_computation(experiment, user)):
        if j < start:
            continue
        if i >= capacity:
            break
        job_command = '%s %s "%s" "%s" "%s"' % (sys.executable, script_path,
                                               exp_name, job_name,
                                               serialize(param))

        script = build_script(job_command, job_name=job_name)
        logger.debug("Script:\n%s" % script)

        start_date = pending_job_update(exp_name, job_name)
        try:
            output = subprocess.check_output(script, shell=True)
            logger.debug("Output:\n%s" % output.decode("utf-8"))
        except CalledProcessError as exception:
            aborted_job_update(exp_name, job_name, start_date, picklify(exception))
            logger.error("Error launching job '%s': %s" % (job_name,
                exception.message), exc_info=True)
            if not force:
                break
        i += 1


    logger.info("Experiment '%s': %d/%d computation(s)" % (exp_name, i, len(experiment)))


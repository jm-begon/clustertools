# -*- coding: utf-8 -*-

"""
"""

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
                   force=False, user=os.environ["USER"],
                   serialize=encode_kwargs, capacity=sys.maxsize):

    exp_name = experiment.name
    logger = logging.getLogger("clustertools")
    logger.info("Launching experiment '%s' with script '%s'" %(experiment, script_path))

    get_storage(exp_name).init()

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
            aborted_job_update(exp_name, job_name, start, picklify(exception))
            logger.error("Error launching job '%s': %s" % (job_name,
                exception.message), exc_info=True)
            if not force:
                break
        if i > capacity:
            break

    logger.info("Experiment '%s': %d/%d computation(s)" % (exp_name, (i+1), len(experiment)))


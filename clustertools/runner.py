# -*- coding: utf-8 -*-

"""
"""

import sys
import os
import subprocess
from subprocess import CalledProcessError
import logging

from clusterlib.scheduler import submit

from .state import PendingState, AbortedState, yield_not_done_computation
from .storage import PickleStorage
from .util import encode_kwargs


__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


def picklify(cpe):
    return PickableCalledProcessError(cpe.cmd, cpe.returncode, cpe.output)


class PickableCalledProcessError(CalledProcessError):
    def __init__(self, cmd="", returncode=0, output=""):
        super(PickableCalledProcessError, self).__init__(returncode, cmd, output)


def run_experiment(experiment, script_path, build_script=submit,
                   force=False, user=os.environ["USER"],
                   serialize=encode_kwargs, capacity=sys.maxsize,
                   start=0, storage_factory=PickleStorage):

    exp_name = experiment.name
    logger = logging.getLogger("clustertools")
    logger.info("Launching experiment '%s' with script '%s'" %(experiment, script_path))

    storage = storage_factory(experiment_name=exp_name).init()

    i = 0
    for j, (comp_name, param) in enumerate(yield_not_done_computation(experiment, user)):
        if j < start:
            continue
        if i >= capacity:
            break
        job_command = '%s %s "%s" "%s" "%s"' % (sys.executable, script_path,
                                               exp_name, comp_name,
                                               serialize(param))

        script = build_script(job_command, job_name=comp_name)
        logger.debug("Script:\n%s" % script)

        state = storage.update_state(PendingState(exp_name, comp_name))

        try:
            output = subprocess.check_output(script, shell=True)
            logger.debug("Output:\n%s" % output)
        except CalledProcessError as exception:
            storage.update_state(state.abort(exception))
            logger.error("Error launching job '%s': %s" % (comp_name,
                         exception.message), exc_info=True)
            if not force:
                break
        i += 1

    logger.info("Experiment '%s': %d/%d computation(s)" % (exp_name, i, len(experiment)))


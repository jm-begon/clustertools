# -*- coding: utf-8 -*-

"""
Module :mod:`database` contains helper function for manipulating the databases

3 databases:
    - Global:
        - Experiments
    - Per experiment
        - Notificaiton
        - Results
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


import os
import logging

from clusterlib.storage import sqlite3_dumps, sqlite3_loads

from .util import get_ct_folder, get_log_folder

__DB_ENV__ = "CLUSTERTOOLS_DB_FOLDER"
__EXPDB__ = "experiments.sqlite3"


#======================= PATHS =======================#

def _get_db_folder():
    try:
        folder = os.environ[__DB_ENV__]
    except KeyError:
        folder = os.path.join(get_ct_folder(), "databases")
        os.environ[__DB_ENV__] = folder
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def get_expdb():
    folder = _get_db_folder()
    return os.path.join(folder, __EXPDB__)

def get_notifdb(exp_name):
    folder = _get_db_folder()
    fname = "notif_"+str(exp_name)+".sqlite3"
    return os.path.join(folder, fname)

def get_resultdb(exp_name):
    fname = "result_"+str(exp_name)+".sqlite3"
    folder = _get_db_folder()
    return os.path.join(folder, fname)


#======================= I/O EXPERIMENTS =======================#

def save_experiment(experiment, overwrite=True):
    name = experiment.name
    db = get_expdb()
    sqlite3_dumps({name: experiment}, db, overwrite=overwrite)


def load_experiments(name=None, *names):
    if name is None:
        names = None
    else:
        names = [name] + list(names)
    db = get_expdb()
    return sqlite3_loads(db, names)


#======================= I/O NOTIFS =======================#

def update_notification(exp_name, dictionary):
    db = get_notifdb(exp_name)
    sqlite3_dumps(dictionary, db, overwrite=True)

def load_notifications(exp_name):
    db = get_notifdb(exp_name)
    return sqlite3_loads(db)

#======================= I/O RESULTS =======================#

def save_result(exp_name, dictionary, overwrite=True):
    db = get_resultdb(exp_name)
    sqlite3_dumps(dictionary, db, overwrite=overwrite)


def load_results(exp_name):
    db = get_resultdb(exp_name)
    return sqlite3_loads(db)


def erase_experiment(exp_name):
    db = get_resultdb(exp_name)
    logger = logging.getLogger("clustertools")
    try:
        os.remove(db)
    except OSError, reason:
        logger.warn("Trouble erasing result database: %s" % reason, exc_info=True)
    db = get_notifdb(exp_name)
    try:
        os.remove(db)
    except OSError, reason:
        logger.warn("Trouble erasing notification database: %s" % reason, exc_info=True)
    log_folder = get_log_folder(exp_name)
    try:
        os.remove(log_folder)
    except OSError, reason:
        logger.warn("Trouble erasing log folder: %s"%reason, exc_info=True)
    # TODO move this to clusterlib
    import sqlite3
    db = get_expdb()
    with sqlite3.connect(db, timeout=7200.0) as connection:
        connection.execute("""DELETE FROM dict WHERE key=%s"""%exp_name)







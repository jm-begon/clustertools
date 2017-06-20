
"""
:mod:`deprecated` contains broken dependency functions for older version
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


import os
import sys
import glob
import shutil
import logging
import collections
from datetime import datetime


from clusterlib.storage import sqlite3_dumps, sqlite3_loads
from .experiment import Datacube

__CT_FOLDER__ = "clustertools_data"
__LOG_ENV__ = "CLUSTERTOOLS_LOGS_FOLDER"
__METALOG__ = "clustertools.log"

__DB_ENV__ = "CLUSTERTOOLS_DB_FOLDER"
__EXPDB__ = "experiments.sqlite3"

__EXP_NAME__ = "Experiment"
__PARAMETERS__ = "Parameters"
__RESULTS__ = "Results"


# from http://stackoverflow.com/questions/2536307/decorators-in-the-python-standard-lib-deprecated-specifically
def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning) #turn off filter
        warnings.warn("Call to deprecated function {}.".format(func.__name__), category=DeprecationWarning, stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning) #reset filter
        return func(*args, **kwargs)

    return new_func


# ====================== VERSION 0.0.1 ====================== #

# ---------------------- from util.py ---------------------- #

def get_ct_folder0_0_1():
    return os.path.join(os.environ["HOME"], __CT_FOLDER__)

def get_log_folder0_0_1(exp_name=None):
    try:
        folder = os.environ[__LOG_ENV__]
    except KeyError:
        folder = os.path.join(get_ct_folder0_0_1(), "logs")
        os.environ[__LOG_ENV__] = folder

    if exp_name is not None:
        folder = os.path.join(folder, exp_name)

    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def get_meta_log_file0_0_1():
    fname = "clustertools_%s.log" % (datetime.now().strftime("%B%Y"))
    return os.path.join(get_log_folder0_0_1(), fname)

def get_log_file0_0_1(exp_name, comp_name):
    """Return the most recent (ctime) matching file"""
    folder = get_log_folder0_0_1(exp_name)
    prefix = os.path.join(folder, comp_name)
    try:
        return max(glob.iglob("%s.*"%prefix), key=os.path.getctime)
    except ValueError:
        return None


def print_log_file0_0_1(exp_name, comp_name, last_lines=None, out=sys.stdout):
    f = get_log_file0_0_1(exp_name, comp_name)
    if f is None:
        logger = logging.getLogger("clustertools.util.print_log_file")
        logger.warn("File '%s' does not exists."%f)
        return
    if last_lines is None:
        with open(f) as fhd:
            out.write(fhd.read())
    else:
        buffer_ = collections.deque(maxlen=last_lines)
        with open(f) as fhd:
            for line in fhd:
                buffer_.append(line)
        for line in buffer_:
            out.write(line)



def purge_logs0_0_1(exp_name, comp_name=None):
    if comp_name is None:
        shutil.rmtree(get_log_folder0_0_1(exp_name))
    else:
        fp = get_log_file0_0_1(exp_name, comp_name)
        if fp is not None:
            os.remove(fp)


# ---------------------- from storage.py ---------------------- #

def _get_db_folder0_0_1():
    try:
        folder = os.environ[__DB_ENV__]
    except KeyError:
        folder = os.path.join(get_ct_folder0_0_1(), "databases")
        os.environ[__DB_ENV__] = folder
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def get_expdb0_0_1():
    folder = _get_db_folder0_0_1()
    return os.path.join(folder, __EXPDB__)

def get_notifdb0_0_1(exp_name):
    folder = _get_db_folder0_0_1()
    fname = "notif_"+str(exp_name)+".sqlite3"
    return os.path.join(folder, fname)

def get_resultdb0_0_1(exp_name):
    fname = "result_"+str(exp_name)+".sqlite3"
    folder = _get_db_folder0_0_1()
    return os.path.join(folder, fname)


def save_experiment0_0_1(experiment, overwrite=True):
    name = experiment.name
    db = get_expdb0_0_1()
    sqlite3_dumps({name: experiment}, db, overwrite=overwrite)


def load_experiments0_0_1(name=None, *names):
    # Special
    if name is None:
        names = None
    else:
        names = [name] + list(names)
    db = get_expdb0_0_1()
    return sqlite3_loads(db, names)


def update_notification0_0_1(exp_name, dictionary):
    db = get_notifdb0_0_1(exp_name)
    sqlite3_dumps(dictionary, db, overwrite=True)

def load_notifications0_0_1(exp_name):
    db = get_notifdb0_0_1(exp_name)
    return sqlite3_loads(db)


def save_result0_0_1(exp_name, dictionary, overwrite=True):
    db = get_resultdb0_0_1(exp_name)
    sqlite3_dumps(dictionary, db, overwrite=overwrite)


def load_results0_0_1(exp_name):
    db = get_resultdb0_0_1(exp_name)
    return sqlite3_loads(db)


def erase_experiment0_0_1(exp_name):
    db = get_resultdb0_0_1(exp_name)
    logger = logging.getLogger("clustertools")
    try:
        os.remove(db)
    except OSError, reason:
        logger.warn("Trouble erasing result database: %s" % reason, exc_info=True)
    db = get_notifdb0_0_1(exp_name)
    try:
        os.remove(db)
    except OSError, reason:
        logger.warn("Trouble erasing notification database: %s" % reason, exc_info=True)
    try:
        log_folder = get_log_folder0_0_1(exp_name)
        os.remove(log_folder)
    except OSError, reason:
        logger.warn("Trouble erasing log folder: %s"%reason, exc_info=True)
    # TODO move this to clusterlib
    try:
        import sqlite3
        db = get_expdb0_0_1()
        entry = (exp_name, )
        with sqlite3.connect(db, timeout=7200.0) as connection:
            connection.execute("""DELETE FROM dict WHERE key=%s"""%entry)
    except Exception, reason:
        logger.warn("Trouble erasing entry in experiment database: %s"%reason, exc_info=True)

# ---------------------- from experiment.py ---------------------- #

def build_result_cube0_0_1(exp_name):
    result = load_results0_0_1(exp_name)
    parameterss = []
    resultss = []
    for d in result.values():
        parameterss.append(d[__PARAMETERS__])
        resultss.append(d[__RESULTS__])
    return Datacube(parameterss, resultss, exp_name)

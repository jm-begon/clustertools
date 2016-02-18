# -*- coding: utf-8 -*-

"""
Module :mod:`database` contains helper function for manipulating the databases

File system
===========
By default everything related to clustertools is located in a folder named
'clustertools_data' (aka ct_folder) in the user home directory. The ct_folder
is structured as followed:
    clustertools_data
    |- logs
    |- exp_XXX
    |   |- logs
    |   |- $result$
    |   |- $notifs$
    |- exp_YYY
        |...
where logs is a folder containing the main logs (not the one corresponding to
the experiments). exp_XXX is the folder related to experiment 'XXX'.
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


import os, sys
import glob
import logging
import collections
from datetime import datetime
try:
    import cPickle as pickle
except ImportError:
    import pickle
import shutil

from clusterlib.storage import sqlite3_dumps, sqlite3_loads
from sqlite3 import OperationalError

from .config import get_ct_folder, get_storage_type



def get_basedir(exp_name):
    ct_folder = get_ct_folder()
    return os.path.join(ct_folder, "exp_%s"%exp_name)


def load_experiment_names():
    res = []
    for path in glob.glob(os.path.join(get_ct_folder(), "exp_*")):
        if not os.path.isdir(path):
            continue
        exp_name = os.path.basename(path)[4:]  # remove 'exp_'
        res.append(exp_name)
    return res


def get_meta_log_file():
    log_folder = os.path.join(get_ct_folder(), "logs")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    fname = "clustertools_%s.log" % (datetime.now().strftime("%B%Y"))
    return os.path.join(log_folder, fname)




#======================= STORAGE MANAGER =======================#

class BaseStorage(object):
    """Database is a folder. Each record is a individual file"""

    def _save(cls, stuff, fpath):
        with open(fpath, "wb") as hdl:
            pickle.dump(stuff, hdl, -1)

    def _load(cls, fpath):
        with open(fpath, "rb") as hdl:
            rtn = pickle.load(hdl)
        return rtn

    def __init__(self, experiment_name):
        self.exp_name = experiment_name
        self.folder = get_basedir(experiment_name)

    def init(self):
        self.makedirs()
        return self

    def _get_notifdb(self):
        return os.path.join(self.folder, "notifications")

    def _get_resultdb(self):
        return os.path.join(self.folder, "results")

    def get_log_folder(self):
        return os.path.join(self.folder, "logs")

    def makedirs(self):
        for folder in [self._get_notifdb(), self._get_resultdb(),
                       self.get_log_folder()]:
            if not os.path.exists(folder):
                os.makedirs(folder)
        return self

    def erase_experiment(self):
        logger = logging.getLogger("clustertools")
        try:
            shutil.rmtree(self.folder)
        except OSError, reason:
            logger.warn("Trouble erasing the databases: %s" % reason,
                        exc_info=True)

    def update_notification(self, comp_name, dictionary):
        fpath = os.path.join(self._get_notifdb(), "%s.pkl"%comp_name)
        self._save(dictionary, fpath)

    def update_notifications(self, comp_names, dictionaries):
        for comp_name, dic in zip(comp_names, dictionaries):
            self.update_notification(comp_name, dic)

    def load_notifications(self):
        res = {}
        for fpath in glob.glob(os.path.join(self._get_notifdb(), "*.pkl")):
            # basename = os.path.basename(fpath)[:-4]   # Remove .pkl
            res.update(self._load(fpath))
        return res

    def save_result(self, comp_name, dictionary, overwrite=True):
        fpath = os.path.join(self._get_resultdb(), "%s.pkl"%comp_name)
        self._save(dictionary, fpath)

    def load_result(self, comp_name):
        fpath = os.os.path.join(self._get_resultdb(), "%s.pkl"%comp_name)
        if os.path.exists(fpath):
            return self._load(fpath)
        return {}

    def load_results(self):
        res = {}
        for fpath in glob.glob(os.path.join(self._get_resultdb(), "*.pkl")):
            # basename = os.path.basename(fpath)[:-4]   # Remove .pkl
            res.update(self._load(fpath))
        return res


    def get_log_file(self, comp_name):
        """Return the most recent (ctime) matching file"""
        folder = self.get_log_folder()
        prefix = os.path.join(folder, comp_name)
        try:
            return max(glob.iglob("%s.*"%prefix), key=os.path.getctime)
        except ValueError:
            return None

    def purge_logs(self, comp_name=None):
        if comp_name is None:
            shutil.rmtree(self.get_log_folder())
        else:
            fp = self.get_log_file(comp_name)
            if fp is not None:
                os.remove(fp)

    def print_log(self, comp_name, last_lines=None, out=sys.stdout):
        f = self.get_log_file(comp_name)
        if f is None:
            logger = logging.getLogger("clustertools.print_log_file")
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






class SQLiteStorage(BaseStorage):

    def _save(cls, stuff, fpath, overwrite=True):
        sqlite3_dumps(stuff, fpath, overwrite=overwrite)

    def _load(cls, fpath, mask=None):
        try:
            tmp = sqlite3_loads(fpath, mask)
        except OperationalError:
            tmp = {}
        return tmp


    def _get_notifdb(self):
        return os.path.join(self.folder, "notifications")+".sqlite3"

    def _get_resultdb(self):
        return os.path.join(self.folder, "results")+".sqlite3"

    def makedirs(self):
        for folder in [self.folder, self.get_log_folder()]:
            if not os.path.exists(folder):
                os.makedirs(folder)
        return self

    def update_notification(self, comp_name, dictionary):
        db = self._get_notifdb()
        self._save(dictionary, db, overwrite=True)

    def update_notifications(self, comp_names, dictionaries):
        db = self._get_notifdb()
        tmp = {}
        for dic in dictionaries:
            tmp.update(dic)
        self._save(tmp, db, overwrite=True)

    def load_notifications(self):
        db = self._get_notifdb()
        return self._load(db)

    def save_result(self, comp_name, dictionary, overwrite=True):
        db = self._get_resultdb()
        self._save(dictionary, db, overwrite=overwrite)

    def load_results(self):
        db = self._get_resultdb()
        return self._load(db)

    def load_result(self, comp_name):
        db = self._get_resultdb()
        return self._load(db, comp_name)

def load_results(exp_name):
    for sto_cls in [BaseStorage, SQLiteStorage]:
        storage = sto_cls(exp_name)
        if os.path.exists(storage._get_resultdb()):
            return storage.load_results()
    return {}


def get_storage(exp_name):
    storage_type = get_storage_type()
    storage = __STORAGE_KW__.get(storage_type)
    if storage:
        return storage(exp_name)
    else:
        logger = logging.getLogger("clustertools.database")
        logger.wran("Unrecognized storage key '%s'. Falling back to BaseStorage." % storage_type, exc_info=True)
        return BaseStorage(exp_name)

def pkl2sqlite(exp_name):
    pkl_sto = BaseStorage(exp_name)
    sq_sto = SQLiteStorage(exp_name)
    # Notificaitons
    notifs = pkl_sto.load_notifications()
    sq_sto.update_notifictions("unused", notifs)
    # Results
    res = pkl_sto.load_results()
    sq_sto.save_result("unused", res)  # Not well encapsulated


def sqlite2pkl(exp_name):
    pkl_sto = BaseStorage(exp_name)
    sq_sto = SQLiteStorage(exp_name)
    # Notificaitons
    notifs = sq_sto.load_notifications()
    comp_names = notifs.keys()
    dictionaries = [{k:notifs[k]} for k in comp_names]
    pkl_sto.update_notifictions(comp_names, dictionaries)
    # Results
    res = sq_sto.load_results()
    for comp_name in res.keys():
        dic = {comp_name: res[comp_name]}
        pkl_sto.save_result(comp_name, dic)  # Not well encapsulated


__STORAGES__ = [BaseStorage, SQLiteStorage]
__STORAGE_KW__ = {"pickle": BaseStorage, "sqlite3":SQLiteStorage}

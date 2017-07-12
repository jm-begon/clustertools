# -*- coding: utf-8 -*-

"""
Module :mod:`database` contains helper function for manipulating the databases
"""

import os
import sys
from abc import ABCMeta, abstractmethod
import glob
import collections
from datetime import datetime
import shutil
import logging
try:
    import cPickle as pickle
except ImportError:
    import pickle


from .config import get_ct_folder


__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


__EXP_NAME__ = "Experiment"
__PARAMETERS__ = "Parameters"
__RESULTS__ = "Results"
__CONTEXT__ = "Context"


class Architecture(object):
    """
    ``Architecture``
    ================
    An ``Architecture`` is responsible for the organization of the experiments
    and logs on the file system.
    In clustertools is located in a folder named 'clustertools_data' (aka
    ct_folder) in the user home directory. The ct_folder is structured as
    followed:
        clustertools_data
        |- logs
        |- exp_XXX
        |   |- logs
        |   |- $result$
        |   |- $notifs$
        |- exp_YYY
            |...
    where logs is a folder containing the main logs (not the ones corresponding to
    the experiments). exp_XXX is the folder related to experiment 'XXX'.
    """
    def __init__(self, ct_folder=None):
        if ct_folder is None:
            ct_folder = get_ct_folder()
        self.ct_folder = ct_folder

    def __repr__(self):
        return "{cls}(ct_folder={folder})".format(cls=self.__class__.__name__,
                                                  folder=self.ct_folder)

    def get_basedir(self, exp_name):
        return os.path.join(self.ct_folder, "exp_%s"%exp_name)

    def load_experiment_names(self):
        res = []
        for path in glob.glob(os.path.join(self.ct_folder, "exp_*")):
            if not os.path.isdir(path):
                continue
            exp_name = os.path.basename(path)[4:]  # remove 'exp_'
            res.append(exp_name)
        return res

    def get_meta_log_file(self):
        log_folder = os.path.join(self.ct_folder, "logs")
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        fname = "clustertools_%s.log" % (datetime.now().strftime("%B%Y"))
        return os.path.join(log_folder, fname)

    def erase_experiment(self, exp_name):
        logger = logging.getLogger("clustertools")
        try:
            path = self.get_basedir(exp_name)
            if os.path.exists(path):
                shutil.rmtree(path)
        except OSError as error:
            logger.warn("Trouble erasing the databases: %s" % error.message,
                        exc_info=True)


# ======================= STORAGE MANAGER ======================= #

class Storage(object):
    """
    ``Storage``
    ===========
    A ``Storage`` objects manages two databases:
    - "notifications" which contains the states of the computations
    - "results" which contains the results of the computations
    and two folders:
    - "logs" which contains the logs of each computations
    - "computations" which contains the serialized lazy computations
    """
    __metaclass__ = ABCMeta

    def __init__(self, experiment_name, architecture=Architecture()):
        self._exp_name = experiment_name
        self._architecture = architecture
        self._folder = architecture.get_basedir(experiment_name)

    def __repr__(self):
        return "{cls}(experiment_name={exp_name}, architecture={architecture})"\
               "".format(cls=self.__class__.__name__,
                         exp_name=self._exp_name,
                         architecture=self._architecture)

    @property
    def exp_name(self):
        return self._exp_name

    @property
    def architecture(self):
        return self._architecture

    @property
    def folder(self):
        return self._folder

    def delete(self):
        self.architecture.erase_experiment(self.exp_name)

    def init(self):
        for folder in self.get_log_folder(), self.get_serialization_folder():
            if not os.path.exists(folder):
                os.makedirs(folder)
        return self

    # |--------------------------- Serialization ----------------------------> #
    def get_serialization_folder(self):
        return os.path.join(self.folder, "computations")

    def serialize(self, computation):
        fpath = os.path.join(self.get_serialization_folder(),
                             computation.comp_name+".pkl")
        with open(fpath, "wb") as hdl:
            pickle.dump(computation, hdl, -1)
        return fpath

    # |--------------------------- Notifications ----------------------------> #
    @abstractmethod
    def update_state(self, state):
        """Save the given state as current state and returns it"""
        pass

    @abstractmethod
    def load_states(self):
        """Return a list of state corresponding to self.exp_name"""
        pass

    # |---------------------------- Result ---------------------------------> #

    def save_result(self, comp_name, parameters, result, context="n/a"):
        # Create the R-dict (legacy format)
        dictionary = {
            comp_name: {
                __EXP_NAME__: self.exp_name,
                __PARAMETERS__: parameters,
                __CONTEXT__: context,
                __RESULTS__: dict(result)
            }
        }
        self._save_result(comp_name, dictionary)

    @abstractmethod
    def _save_result(self, comp_name, dictionary):
        """Save the given dictionary as proxy for the result"""
        pass

    def load_result(self, comp_name):
        res = self._load_result(comp_name)
        if len(res) == 0:
            return {}
        return res[comp_name][__RESULTS__]

    @abstractmethod
    def _load_result(self, comp_name):
        """load and return the proxy result"""
        pass

    def load_params_and_results(self, **default_meta):
        """
        default_meta: mapping str -> str
            The (potentially) missing metadata

        Return
        ------
        (parameters_ls, results_ls)
        parameters_ls: list of dicts (size: nb of computations)
            parameters_ls[i] is the dictionary of parameters of the ith
            computation. The dictionary is a mapping str (name of the
            parameters) -> value of the parameter
        result_ls: list of dicts (size: nb of computations)
            result_ls[i] is the dictionary of metrics of the ith
            computation. The dictionary is a mapping str (name of the
            metric) -> value of the metric
        """
        parameters_ls = []
        results_ls = []
        for fpath in glob.glob(os.path.join(self._get_result_db(), "*.pkl")):
            comp = self._load(fpath).values()[0]
            results_ls.append(comp[__RESULTS__])
            p = comp[__PARAMETERS__]
            for k,v in default_meta.items():
                if k not in p:
                    p[k] = v
            parameters_ls.append(p)
        return parameters_ls, results_ls

    # |---------------------------- Logs ---------------------------------> #

    def get_log_folder(self):
        return os.path.join(self.folder, "logs")

    def get_log_prefix(self, comp_name, *suffix):
        folder = self.get_log_folder()
        prefix = os.path.join(folder, comp_name, *suffix)
        return prefix

    def get_last_log_file(self, comp_name):
        """Return the most recent (ctime) matching file"""
        try:
            return max(glob.iglob("%s.*" % self.get_log_prefix(comp_name)),
                       key=os.path.getctime)
        except ValueError:
            return None

    def purge_logs(self, comp_name=None):
        if comp_name is None:
            shutil.rmtree(self.get_log_folder())
        else:
            fp = self.get_last_log_file(comp_name)
            if fp is not None:
                os.remove(fp)

    def print_log(self, comp_name, last_lines=None, out=sys.stdout):
        f = self.get_last_log_file(comp_name)
        if f is None:
            logger = logging.getLogger("clustertools.storage.print_log_file")
            logger.warn("File '{file}' does not exists ({comp_name})."
                        "".format(file=f, comp_name=comp_name))
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


class PickleStorage(Storage):
    """Databases are folders. Each record is an individual pickle file.
    Implements a backup mechanism for results to prevent long writes from
    being interrupted
    """

    @classmethod
    def _save(cls, stuff, fpath):
        with open(fpath, "wb") as hdl:
            pickle.dump(stuff, hdl, -1)

    @classmethod
    def _raw_load(cls, fpath):
        with open(fpath, "rb") as hdl:
            return pickle.load(hdl)

    @classmethod
    def _load(cls, fpath):
        try:
            rtn = cls._raw_load(fpath)
        except EOFError:
            logger = logging.getLogger("clustertools.storage")
            logger.error("End of file encountered in '%s'" % fpath)
            return {}
        except:
            logging.exception("Error while loading file '%s'" % fpath)
            return {}
        return rtn

    def __init__(self, experiment_name, architecture=Architecture()):
        super(PickleStorage, self).__init__(experiment_name, architecture)

    def init(self):
        super(PickleStorage, self).init()
        for folder in self._get_notif_db(), self._get_result_db(), \
                self._get_tmp_folder():
            if not os.path.exists(folder):
                os.makedirs(folder)
        return self

    def _get_notif_db(self):
        return os.path.join(self.folder, "notifications")

    def _get_result_db(self):
        return os.path.join(self.folder, "results")

    def _get_tmp_folder(self):
        return os.path.join(self.folder, "temp")

    # |--------------------------- Notifications ----------------------------> #

    def update_state(self, state):
        fpath = os.path.join(self._get_notif_db(), "%s.pkl" % state.comp_name)
        self._save(state, fpath)
        return state

    def load_states(self):
        res = []
        for fpath in glob.glob(os.path.join(self._get_notif_db(), "*.pkl")):
            res.append(self._load(fpath))
        return res

    # |---------------------------- Results -----------------------------> #

    def _tmp_path(self, comp_name):
        return os.path.join(self._get_tmp_folder(), "%s.pkl" % comp_name)

    def _bc_path(self, comp_name):
        return os.path.join(self._get_tmp_folder(), "%s.bc.pkl" % comp_name)

    def _result_path(self, comp_name):
        return os.path.join(self._get_result_db(), "%s.pkl" % comp_name)

    def _save_result(self, comp_name, dictionary):
        # Build paths
        tmp_path = self._tmp_path(comp_name)
        bc_path = self._bc_path(comp_name)
        fpath = self._result_path(comp_name)
        # Write to disk in temp
        self._save(dictionary, tmp_path)
        # Back up old results
        if os.path.exists(fpath):
            shutil.move(fpath, bc_path)
        # Place new file at the right place
        shutil.move(tmp_path, fpath)

    def restore_back_up(self, comp_name):
        bc_path = self._bc_path(comp_name)
        fpath = self._result_path(comp_name)
        shutil.move(bc_path, fpath)

    def _load_result(self, comp_name):
        fpath = self._result_path(comp_name)
        if os.path.exists(fpath):
            return self._load(fpath)
        return {}


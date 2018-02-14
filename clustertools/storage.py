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
    By default, clustertools is located in a folder named 'clustertools_data'
    (aka ct_folder) in the user home directory. The ct_folder is structured as
    followed:
        clustertools_data
        |- logs
        |- exp_XXX
        |   |- logs
        |   |- $result$
        |   |- $notifs$
        |- exp_YYY
            |...
    where `logs` is a folder containing the main logs (not the ones corresponding
    to the experiments).  exp_XXX is the folder related to experiment 'XXX'.
    """
    def __init__(self, ct_folder=None):
        if ct_folder is None:
            ct_folder = get_ct_folder()
        self.ct_folder = ct_folder

    def __repr__(self):
        return "{cls}(ct_folder={folder})".format(cls=self.__class__.__name__,
                                                  folder=repr(self.ct_folder))

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
            logger.warning("Trouble erasing the databases: {}"
                           "".format(repr(error)),
                           exc_info=True)


# ============================== STORAGE MANAGER ============================= #

class Storage(object):
    """
    ``Storage``
    ===========
    A ``Storage`` objects manages two databases:
    - "notifications" which contains the states of the computations
    - "results" which contains the results of the computations
    and two folders:
    - "logs" which contains the logs of each computations
    - "mess" which can be used to store other things
    """
    __metaclass__ = ABCMeta

    def __init__(self, experiment_name, architecture=Architecture()):
        self._exp_name = experiment_name
        self._architecture = architecture
        self._folder = architecture.get_basedir(experiment_name)

    def __repr__(self):
        return "{cls}(experiment_name={exp_name}, architecture={architecture})"\
               "".format(cls=self.__class__.__name__,
                         exp_name=repr(self._exp_name),
                         architecture=repr(self._architecture))

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
        for folder in self.get_log_folder(), \
                      self.get_messy_path():
            if not os.path.exists(folder):
                os.makedirs(folder)
        return self

    # |-------------------------------- Mess --------------------------------> #

    def get_messy_path(self, fname=None):
        if fname is None:
            return os.path.join(self.folder, "mess")
        else:
            return os.path.join(self.folder, "mess", fname)
    # TODO: decouple and re-use computation comp_name

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
    # Results are saved as R-dict, a dictionary where the key correspond to
    # a computation name and the value is another dictionary (the result proxy)
    # whose key-value mapping represent information regarding the results
    # (namely, the experience name, the parameters of the computation, the
    # context and the actual results)
    def save_result(self, comp_name, parameters, result, context="n/a"):
        # Create the R-dict (legacy format)
        r_dict = {
            comp_name: {
                __EXP_NAME__: self.exp_name,
                __PARAMETERS__: parameters,
                __CONTEXT__: context,
                __RESULTS__: dict(result)
            }
        }
        self._save_r_dict(comp_name, r_dict)

    @abstractmethod
    def _save_r_dict(self, comp_name, r_dict):
        """Save the given r_dict singleton corresponding to the given
        computation"""
        pass

    def load_result(self, comp_name):
        res = self._load_r_dict(comp_name)
        try:
            if len(res) == 0:
                return {}
        except:
            return {}
        return res[comp_name][__RESULTS__]

    @abstractmethod
    def _load_r_dict(self, comp_name):
        """load and return the r_dict singleton of the given computation"""
        pass

    @abstractmethod
    def _load_r_dicts(self):
        """load and return the r_dict of all the computations"""
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
        for result_proxy in self._load_r_dicts().values():
            results_ls.append(result_proxy[__RESULTS__])
            p = result_proxy[__PARAMETERS__]
            for k, v in default_meta.items():
                if k not in p:
                    p[k] = v
            parameters_ls.append(p)
        return parameters_ls, results_ls

    # |---------------------------- Logs ---------------------------------> #

    def get_log_folder(self):
        return os.path.join(self.folder, "logs")

    def get_log_prefix(self, comp_name, suffix=""):
        folder = self.get_log_folder()
        prefix = os.path.join(folder, comp_name+suffix)
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
            logger.warning("File '{file}' does not exists ({comp_name})."
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


# ============================== PICKLE MANAGER ============================== #
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
            logger.error("End of file encountered in '{}'".format(fpath))
            return {}
        except Exception as exception:
            logging.exception("Error while loading file '{}'. Reason: {}"
                              .format(fpath, repr(exception)))
            return {}
        return rtn

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
            loaded = self._load(fpath)
            try:
                if len(loaded) > 0:
                    res.append(loaded)
            except:
                pass
            res.append(loaded)
        return res

    # |---------------------------- Results -----------------------------> #

    def _tmp_path(self, comp_name):
        return os.path.join(self._get_tmp_folder(), "%s.pkl" % comp_name)

    def _bc_path(self, comp_name):
        return os.path.join(self._get_tmp_folder(), "%s.bc.pkl" % comp_name)

    def _result_path(self, comp_name):
        return os.path.join(self._get_result_db(), "%s.pkl" % comp_name)

    def _save_r_dict(self, comp_name, r_dict):
        # Build paths
        tmp_path = self._tmp_path(comp_name)
        bc_path = self._bc_path(comp_name)
        fpath = self._result_path(comp_name)
        # Write to disk in temp
        self._save(r_dict, tmp_path)
        # Back up old results
        if os.path.exists(fpath):
            shutil.move(fpath, bc_path)
        # Place new file at the right place
        shutil.move(tmp_path, fpath)

    def restore_back_up(self, comp_name):
        bc_path = self._bc_path(comp_name)
        fpath = self._result_path(comp_name)
        shutil.move(bc_path, fpath)

    def _load_r_dict(self, comp_name):
        fpath = self._result_path(comp_name)
        if os.path.exists(fpath):
            return self._load(fpath)
        return {}

    def _load_r_dicts(self):
        """load and return all the proxy results"""
        r_dict = {}
        for fpath in glob.glob(os.path.join(self._get_result_db(), "*.pkl")):
            r_dict.update(self._load(fpath))
        return r_dict


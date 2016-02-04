# -*- coding: utf-8 -*-

"""
Module :mod:`config` contains the configurable features
"""

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"

import os
import yaml


__CT_FOLDER__ = "clustertools_data"
__CONF_NAME__ = "config.yaml"


def _get_default_config():
    return {
        "Main": {
            "folder": __CT_FOLDER__,
        },
        "Storage":{
            "default":"sqlite3"
        },
    }

def get_ct_folder(conf=_get_default_config()):
    folder_name = conf["Main"]["folder"]
    return os.path.join(os.environ["HOME"], folder_name)


def get_config():
    fpath = os.path.join(get_ct_folder(), __CONF_NAME__)
    if not os.path.exists(fpath):
        return _get_default_config()
    with open(fpath) as hdl:
        config =  yaml.load(hdl)
    return config


def dump_config(conf=_get_default_config(), fname=__CONF_NAME__, erase=False):
    folder = get_ct_folder()
    if not os.path.exists(folder):
        os.makedirs(folder)
    fpath = os.path.join(folder, fname)
    if not erase and os.path.exists(fpath):
        return
    with open(fpath, "w") as hdl:
        yaml.dump(conf, hdl)


def get_storage_type():
    return get_config()["Storage"]["default"]




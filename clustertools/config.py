# -*- coding: utf-8 -*-

"""
Module :mod:`config` contains the configurable features
"""

import os

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


__CT_FOLDER__ = "clustertools_data"

__CT_FOLDER_ENVVAR__ = "CT_FOLDER"             # environment variable for the folder
__CT_ENVIRONMENT_ENVVARS__ = "CT_ENVIRONMENT"  # env var for preferred environment


def get_ct_folder():
    folder = os.environ.get(__CT_FOLDER_ENVVAR__)
    if folder is None:
        folder = os.path.join(os.path.expanduser("~"), __CT_FOLDER__)
    return folder


def get_default_environment(environment_cls=None):
    if environment_cls is not None:
        return environment_cls

    from .environment import __CT_ENVIRONMENTS__

    # Check environment variable
    env_name_var = os.environ.get(__CT_ENVIRONMENT_ENVVARS__)
    if env_name_var is not None:
        for env_name, environment_cls in __CT_ENVIRONMENTS__:
            if env_name == env_name_var:
                return environment_cls

    # Check config file
    # TODO later

    # Check what exists
    for _, environment_cls in __CT_ENVIRONMENTS__:
        if environment_cls.is_usable():
            return environment_cls



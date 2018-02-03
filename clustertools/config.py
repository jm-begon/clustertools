# -*- coding: utf-8 -*-

"""
Module :mod:`config` contains the configurable features
"""

import os

__author__ = "Begon Jean-Michel <jm.begon@gmail.com>"
__copyright__ = "3-clause BSD License"


__CT_FOLDER__ = "clustertools_data"
__CT_ENV__ = "CT_FOLDER"


def get_ct_folder():
    folder = os.environ.get(__CT_ENV__)
    if folder is None:
        folder = os.path.join(os.path.expanduser("~"), __CT_FOLDER__)
    return folder


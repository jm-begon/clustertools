# -*- coding: utf-8 -*-
#!/usr/bin/env python

# Authors: Jean-Michel Begon
#
# License: BSD 3 clause

from distutils.core import setup

import clustertools

NAME = 'clustertools'
VERSION = clustertools.__version__
AUTHOR = "Jean-Michel Begon"
AUTHOR_EMAIL = "jm.begon@gmail.com"
URL = 'https://github.com/jm-begon/clustertools/'
DESCRIPTION = 'Toolkit to run experiments on supercomputers'
with open('README.md') as f:
    LONG_DESCRIPTION = f.read()
CLASSIFIERS = [
    'Development Status :: 2 - Pre-Alp  ha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Education',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Topic :: Scientific/Engineering',
    'Topic :: Utilities',
    'Topic :: Software Development :: Libraries',
]

if __name__ == '__main__':
    from clustertools.config import dump_config
    dump_config()
    setup(name=NAME,
          version=VERSION,
          author=AUTHOR,
          author_email=AUTHOR_EMAIL,
          url=URL,
          description=DESCRIPTION,
          long_description=LONG_DESCRIPTION,
          license='BSD3',
          classifiers=CLASSIFIERS,
          platforms='any',
          install_requires=['clusterlib', 'nose'],
          packages=['clustertools', 'clustertools.test'],
          scripts=['bin/ct_count', 'bin/ct_sync', 'bin/ct_001to002',
                   'bin/ct_remote'])


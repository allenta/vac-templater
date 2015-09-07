#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
VAC Templater
=============

VAC (Varnish Administration Console) Templater is a simple server and web UI
designed to allow non-technical users to graphically modify and deploy Varnish
Cache configurations. VAC Templater depends on the VAC API to discover VCL files
and to execute deployments. A Varnish Plus subscription is required to get
access to the VAC.

Check out https://github.com/allenta/vac-templater for a detailed description,
extra documentation, and other useful information.

:copyright: (c) 2015 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import os
import sys
from setuptools import setup, find_packages

if sys.version_info < (2, 7):
    raise Exception('VAC Templater requires Python 2.7 or higher.')

root = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(root, 'requirements.txt')) as file:
    install_requires = file.read().splitlines()

with open(os.path.join(root, 'version.txt')) as file:
    version = file.read().strip()

extra = {}

if sys.version_info[0] == 3:
    extra['use_2to3'] = True

setup(
    name='vac-templater',
    version=version,
    author='Allenta Consulting S.L.',
    author_email='info@allenta.com',
    packages=find_packages(),
    include_package_data=True,
    url='https://www.allenta.com',
    description='VAC Templater.',
    long_description=__doc__,
    license='GPL',
    entry_points={
        'console_scripts': [
            'vac-templater = vac_templater.runner:main',
        ],
    },
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
    ],
    install_requires=install_requires,
    **extra
)

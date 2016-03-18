# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import


def _set_spooler():
    import uwsgi
    from vac_templater.tasks.base import spooler
    uwsgi.spooler = spooler


def _init_django():
    from django.conf import settings
    if settings.configured:
        import django
        django.setup()


def _init_mediagenerator():
    from mediagenerator.settings import MEDIA_DEV_MODE
    if MEDIA_DEV_MODE:
        from mediagenerator.utils import _refresh_dev_names
        _refresh_dev_names()


import vac_templater
_set_spooler()
_init_django()
_init_mediagenerator()

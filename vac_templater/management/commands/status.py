# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import os
import sys
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Shows daemon service status.'

    def handle(self, *args, **options):
        if os.path.isfile(settings.UWSGI_PIDFILE):
            with open(settings.UWSGI_PIDFILE, 'r') as pidfile:
                os.kill(int(pidfile.read()), 10)
        else:
            sys.exit(1)

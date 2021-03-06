# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import os
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Reloads daemon workers.'

    def handle(self, *args, **options):
        os.execvp('uwsgi', [
            'uwsgi',
            '--reload', settings.UWSGI_PIDFILE])

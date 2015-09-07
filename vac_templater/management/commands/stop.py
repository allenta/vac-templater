# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import os
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Stops daemon workers.'

    def handle(self, *args, **options):
        os.execvp('uwsgi', [
            'uwsgi',
            '--stop', settings.UWSGI_PIDFILE])

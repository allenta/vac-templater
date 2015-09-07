# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import os
import sys
import tempfile
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from vac_templater import tasks


class Command(BaseCommand):
    help = 'Starts daemon workers.'

    def handle(self, *args, **options):
        call_command('upgrade')

        args = [
            'uwsgi',
            '--module', 'vac_templater.wsgi:application',
            '--master',
            '--harakiri', '60',
            '--harakiri-verbose',
            '--buffer-size', '32768',
            '--limit-post', '1048576',
            '--post-buffering', '8192',
            '--max-requests', '1000',
            '--reload-mercy', '4',
            '--listen', '100',
            '--enable-threads',
            '--vacuum',
            '--chdir', tempfile.gettempdir(),
            '--spooler', settings.UWSGI_SPOOLER,
            '--spooler-ordered',
            '--spooler-processes', '2',
            '--spooler-max-tasks', '1000',
            '--spooler-harakiri', str(tasks.Task.TIMEOUT),
            '--spooler-frequency', '1',
            '--import', 'vac_templater.uwsgi',
            '--logformat', '%(addr) - %(user) [%(ltime)] "%(method) %(uri) %(proto)" %(status) %(size) "%(referer)" "%(uagent)"',
            '--processes', str(settings.UWSGI_PROCESSES),
            '--http', settings.UWSGI_BIND,
            '--uid', settings.UWSGI_USER,
            '--gid', settings.UWSGI_GROUP,
            '--pidfile2', settings.UWSGI_PIDFILE,
            '--logto2', settings.UWSGI_LOGFILE,
        ]
        for mtype in [
                'text/css',                       # .css
                'application/javascript',         # .js
                'image/jpeg',                     # .jpeg
                'image/png',                      # .png
                'image/gif',                      # .gif
                'application/x-font-woff',        # .woff
                'application/vnd.ms-fontobject',  # .eot
                'application/font-sfnt',          # .otf
                'image/svg+xml',                  # .svg
                'application/font-woff']:         # .ttf
            args.append('--static-expires-type')
            args.append(mtype + '=86400')
        if settings.UWSGI_DAEMONIZE:
            args = args + [
                '--daemonize',
                '/dev/null',
            ]
        if settings.IS_PRODUCTION:
            args = args + [
                '--static-map', settings.PRODUCTION_MEDIA_URL.rstrip('/') + '=' + os.path.join(settings.ROOT, 'assets'),
            ]
        else:
            args = args + [
                '--static-map', settings.DEV_MEDIA_URL.rstrip('/') + '=' + os.path.join(settings.ROOT, 'static'),
            ]
        if not settings.DEBUG:
            args = args + [
                '--disable-logging',
                '--spooler-quiet',
            ]

        os.environ['PYTHONPATH'] = ':'.join(sys.path)

        os.execvp('uwsgi', args)

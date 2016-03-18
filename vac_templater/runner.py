#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import os
import random
import string
import sys
from path import path


def default_config():
    return '''
# General settings.
[global]
base_url: http://vac-templater.domain.com
logfile: /var/log/vac-templater/vac-templater.log
timezone: Europe/Madrid
secret_key: %(secret_key)s
debug: false
development: false

# uWSGI settings.
[uwsgi]
daemonize: true
bind: 127.0.0.1:8001
processes: 8
user: www-data
group: www-data
pidfile: /var/run/vac-templater/vac-templater.pid
logfile: /var/log/vac-templater/vac-templater.uwsgi.log
spooler: /var/run/vac-templater

# VAC settings.
[vac]
location: http://vac.domain.com:8000
api: http://127.0.0.1:8000
user: vac
password: vac

# SSL settings. Enable SSL only for proxied VAC Templater deployments.
[ssl]
enabled: false
header_name: HTTP_X_FORWARDED_PROTO
header_value: https

# SQLite database settings.
[database]
location: /var/lib/vac-templater/vac-templater.db

# Mailing settings.
[email]
host: 127.0.0.1
port: 25
user:
password:
tls: false
from: noreply@example.com
subject_prefix: [VAC Templater]
contact: info@example.com
notifications: alice@example.com, bob@example.com

# i18n settings. English (en) is the only available language at the moment.
[i18n]
default: en
    ''' % {
        'secret_key': ''.join(
            random.choice(string.ascii_letters + string.digits)
            for i in range(64))
    }


def main():
    # Add the root of the project to the beginning of Python path.
    sys.path.insert(0, str(path(__file__).abspath().dirname().dirname()))

    # Keep the Python interpreter from automatically including this
    # script's current directory (the 'vac_templater' folder inside of the root
    # of the project) as it might lead to collisions in the modules namespace
    # which would result in bugs hard to debug.
    try:
        sys.path.remove(str(path(__file__).abspath().dirname()))
    except:
        pass

    # Execute command.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vac_templater.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()

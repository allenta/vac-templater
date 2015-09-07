# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import ConfigParser
import os
import re
import sys
from cStringIO import StringIO
from django.contrib.messages import constants as message_constants
from path import path
from vac_templater.runner import default_config

###############################################################################
## INITIALIZATIONS.
###############################################################################

ROOT = path(__file__).abspath().dirname()

# Execute initializations in the base module.
import vac_templater

# This is defined here as a do-nothing function because we can't import
# django.utils.translation -- that module depends on the settings.
ugettext = lambda s: s

###############################################################################
## CONFIGURATION.
###############################################################################

_config_filename = os.environ.get('VAC_TEMPLATER_CONF', '/etc/vac-templater.conf')
_config = ConfigParser.ConfigParser()
_config.readfp(StringIO(default_config()))
try:
    _config.read([_config_filename])
except:
    sys.exit("Error: failed to load configuration file '%(file)s'." % {
        'file': _config_filename,
    })

###############################################################################
## ENVIRONMENT.
###############################################################################

DEBUG = _config.getboolean('global', 'debug')

if _config.getboolean('global', 'development'):
    ENVIRONMENT = 'development'
    IS_PRODUCTION = False
else:
    ENVIRONMENT = 'production'
    IS_PRODUCTION = True

###############################################################################
## DATABASES.
###############################################################################

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _config.get('database', 'location'),
    }
}

###############################################################################
## CACHES.
###############################################################################

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache',
        'MAX_ENTRIES': 1000,
    }
}

###############################################################################
## SSL.
###############################################################################

HTTPS_ENABLED = _config.getboolean('ssl', 'enabled')
SECURE_PROXY_SSL_HEADER = (
    _config.get('ssl', 'header_name'),
    _config.get('ssl', 'header_value'),
)

###############################################################################
## TEMPLATES.
###############################################################################

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': (
            ROOT / 'templates',
        ),
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': (
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.csrf',
                'django.template.context_processors.request',
                'vac_templater.context_processors.messages',
                'vac_templater.context_processors.page_id',
                'vac_templater.context_processors.is_production',
            ),
            'loaders': (
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ),
        },
    },
]

###############################################################################
## MIDDLEWARE.
###############################################################################

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'vac_templater.middleware.CustomizationsMiddleware',
    'vac_templater.middleware.SSLRedirectMiddleware',
    'mediagenerator.middleware.MediaMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'vac_templater.middleware.MessagingMiddleware',
    'vac_templater.middleware.VersionMiddleware',
    'vac_templater.middleware.AjaxRedirectMiddleware',
)

###############################################################################
## APPS.
###############################################################################

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'mediagenerator',
    'vac_templater',
)

###############################################################################
## SESSIONS & CSRF.
###############################################################################

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = 'sid'
SESSION_COOKIE_SECURE = HTTPS_ENABLED
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False

CSRF_COOKIE_NAME = 'csrf'
CSRF_COOKIE_SECURE = HTTPS_ENABLED

###############################################################################
## AUTHENTICATION.
###############################################################################

AUTH_USER_MODEL = 'vac_templater.User'
AUTHENTICATION_BACKENDS = ('vac_templater.helpers.auth.VACBackend',)

LOGIN_URL = 'user:login'
LOGOUT_URL = 'user:logout'
LOGIN_REDIRECT_URL = 'home'

###############################################################################
## MESSAGES.
###############################################################################

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
MESSAGE_LEVEL = message_constants.INFO

###############################################################################
## MEDIAGENERATOR.
##   - http://www.allbuttonspressed.com/projects/django-mediagenerator
###############################################################################

MEDIA_DEV_MODE = not IS_PRODUCTION
DEV_MEDIA_URL = '/dev/assets/'
PRODUCTION_MEDIA_URL = '/assets/'

GLOBAL_MEDIA_DIRS = (
    ROOT / 'static',
)

GENERATED_MEDIA_DIR = ROOT / 'assets'
GENERATED_MEDIA_NAMES_MODULE = 'vac_templater.assets_mapping'
GENERATED_MEDIA_NAMES_FILE = ROOT / 'assets_mapping.py'

COPY_MEDIA_FILETYPES = (
    'gif', 'jpg', 'jpeg', 'png', 'svg', 'svgz', 'ico', 'swf', 'ttf', 'otf',
    'eot', 'woff', 'woff2', 'json',
)

MEDIA_BUNDLES = (
    ('default-bundle.css',
        'vac-templater/default/js/plugins/jquery-ui/jquery-ui.css',
        'vac-templater/default/js/plugins/jquery-ui/jquery-ui.structure.css',
        'vac-templater/default/js/plugins/jquery-ui/jquery-ui.theme.css',
        'vac-templater/default/js/plugins/select2/select2.css',
        'vac-templater/default/css/plugins/bootstrap/bootstrap.css',
        'vac-templater/default/js/plugins/bootstrap-datetimepicker/bootstrap-datetimepicker.css',
        'vac-templater/default/css/main.scss'),
    ('default-bundle.js',
        'vac-templater/default/js/plugins/jquery.once.js',
        'vac-templater/default/js/plugins/jquery.form.js',
        'vac-templater/default/js/plugins/jquery.notify.js',
        'vac-templater/default/js/plugins/select2/select2.js',
        {
            'filter': 'vac_templater.helpers.mediagenerator.I18NFile',
            'placeholder': '##LANGUAGE##',
            'file': 'vac-templater/default/js/plugins/select2/i18n/##LANGUAGE##.js',
        },
        'vac-templater/default/js/plugins/moment/moment.js',
        {
            'filter': 'vac_templater.helpers.mediagenerator.I18NFile',
            'placeholder': '##LANGUAGE##',
            'file': 'vac-templater/default/js/plugins/moment/i18n/##LANGUAGE##.js',
        },
        'vac-templater/default/js/plugins/bootstrap-datetimepicker/bootstrap-datetimepicker.js',
        'vac-templater/default/js/main.js',
        'vac-templater/default/js/notifications.js',
        'vac-templater/default/js/ajax.js',
        'vac-templater/default/js/behaviors.js',
        'vac-templater/default/js/commands.js',
        'vac-templater/default/js/partials.js'),
    ('default-bootstrap.js',
        {'filter': 'vac_templater.helpers.mediagenerator.I18N'},
        {'filter': 'mediagenerator.filters.media_url.MediaURL'},
        'vac-templater/default/js/plugins/jquery.js',
        'vac-templater/default/js/plugins/jquery-ui/jquery-ui.js',
        'vac-templater/default/js/plugins/bootstrap/bootstrap.js',
        'vac-templater/default/js/bootstrap.js'),
)

ROOT_MEDIA_FILTERS = {
    'js': 'mediagenerator.filters.yuicompressor.YUICompressor',
    'css': 'mediagenerator.filters.yuicompressor.YUICompressor',
}

SASS_FRAMEWORKS = (
    'compass',
)

YUICOMPRESSOR_PATH = os.environ.get('YUICOMPRESSOR_PATH', None)

###############################################################################
## LOGGING.
###############################################################################

SQL_LOGGING = DEBUG
TEMPLATE_DEBUG = DEBUG


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'handlers': ['logfile'],
        'level': 'WARNING',
    },
    'formatters': {
        'verbose': {
            'format':
                '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d '
                '%(message)s'
        },
    },
    'handlers': {
        'logfile': {
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': _config.get('global', 'logfile'),
        },
    },
    'loggers': {
        'vac-templater': {
            'handlers': ['logfile'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
    }
}

###############################################################################
## TESTS.
###############################################################################

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

###############################################################################
## I18N.
###############################################################################

LOCALE_PATHS = (
    ROOT / 'locale',
)
LANGUAGE_CODE = _config.get('i18n', 'default')

LANGUAGES = (
    ('en', ugettext('English')),
)

###############################################################################
## EMAIL.
###############################################################################

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = _config.get('email', 'host')
EMAIL_PORT = _config.getint('email', 'port')
EMAIL_HOST_USER = _config.get('email', 'user')
EMAIL_HOST_PASSWORD = _config.get('email', 'password')
EMAIL_USE_TLS = _config.getboolean('email', 'tls')

DEFAULT_FROM_EMAIL = _config.get('email', 'from')
DEFAULT_BCC_EMAILS = []

SERVER_EMAIL = _config.get('email', 'from')

EMAIL_SUBJECT_PREFIX = _config.get('email', 'subject_prefix') + ' '
CONTACT_EMAIL = _config.get('email', 'contact')

###############################################################################
## POWER USERS.
###############################################################################

ADMINS = [
    (
        'VAC Templater notifications',
        email,
    ) for email in re.split(r'\s*,\s*', _config.get('email', 'notifications'))
]

MANAGERS = ADMINS

###############################################################################
## VERSION.
###############################################################################

VERSION = {
    'assets': {'major': 1, 'minor': 1},
    'js': {'major': 1, 'minor': 1},
    'css': {'major': 1, 'minor': 1},
}

###############################################################################
## UWSGI.
###############################################################################

UWSGI_DAEMONIZE = _config.getboolean('uwsgi', 'daemonize')
UWSGI_BIND = _config.get('uwsgi', 'bind')
UWSGI_PROCESSES = _config.getint('uwsgi', 'processes')
UWSGI_USER = _config.get('uwsgi', 'user')
UWSGI_GROUP = _config.get('uwsgi', 'group')
UWSGI_PIDFILE = _config.get('uwsgi', 'pidfile')
UWSGI_LOGFILE = _config.get('uwsgi', 'logfile')
UWSGI_SPOOLER = _config.get('uwsgi', 'spooler')

###############################################################################
## VAC.
###############################################################################

VAC_LOCATION = _config.get('vac', 'location')
VAC_API = _config.get('vac', 'api')
VAC_USER = _config.get('vac', 'user')
VAC_PASSWORD = _config.get('vac', 'password')

###############################################################################
## MISC.
###############################################################################

ALLOWED_HOSTS = ['*']

BASE_URL = _config.get('global', 'base_url').rstrip('/')
if not BASE_URL.startswith('http'):
    BASE_URL = 'http://%s' % BASE_URL

ROOT_URLCONF = 'vac_templater.urls'
WSGI_APPLICATION = 'vac_templater.wsgi.application'

TIME_ZONE = _config.get('global', 'timezone')
USE_I18N = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
USE_TZ = True
USE_ETAGS = False

SECRET_KEY = _config.get('global', 'secret_key')

DEFAULT_CONTENT_TYPE = 'text/html'
DEFAULT_CHARSET = 'utf-8'

FILE_CHARSET = 'utf-8'

SEND_BROKEN_LINK_EMAILS = False

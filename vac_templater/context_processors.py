# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import json
from django.conf import settings
from django.utils import formats
from vac_templater.helpers.views import get_messages


def datetime_format(request):
    return {
        'datetime_format': formats.get_format('DATETIME_INPUT_FORMATS')[0],
    }


def messages(request):
    return {'messages': json.dumps(get_messages(request))}


def page_id(request):
    return {'page_id': request.page_id}


def is_production(request):
    return {'is_production': settings.IS_PRODUCTION}

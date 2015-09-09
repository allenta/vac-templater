# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import datetime
import decimal
import json
from django.db import models
from django.utils.timezone import is_aware
from vac_templater.helpers.vac_templater_config import (
    VACTemplaterDuration, VACTemplaterACL)


class JSONField(models.Field):
    '''Simple JSON field.

        - https://github.com/bradjasper/django-jsonfield

    '''
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, basestring):
            try:
                return json.loads(value, cls=JSONDecoder)
            except ValueError:
                pass
        return value

    def get_prep_value(self, value):
        if isinstance(value, basestring):
            return value
        if self.null and value is None:
            return None
        return json.dumps(value, cls=JSONEncoder)

    def get_internal_type(self):
        return 'TextField'


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, VACTemplaterACL):
            return {
                'VACTemplaterACL': (
                    o.acls,
                ),
            }
        if isinstance(o, VACTemplaterDuration):
            return {
                'VACTemplaterDuration': (
                    o.amount, o.granularity,
                ),
            }
        if isinstance(o, datetime.datetime):
            if is_aware(o):
                import pytz
                o.astimezone(pytz.UTC).replace(tzinfo=None)
            return {
                'datetime.datetime': (
                    o.year, o.month, o.day,
                    o.hour, o.minute, o.second, o.microsecond,
                ),
            }
        elif isinstance(o, datetime.date):
            return {
                'datetime.date': (
                    o.year, o.month, o.day
                ),
            }
        elif isinstance(o, datetime.time):
            if is_aware(o):
                raise ValueError(
                    'JSON can\'t represent timezone-aware times.')
            return {
                'datetime.time': (
                    o.hour, o.minute, o.second, o.microsecond,
                ),
            }
        elif isinstance(o, (decimal.Decimal)):
            return {
                'decimal.Decimal': str(o),
            }
        else:
            return super(JSONEncoder, self).default(o)


class JSONDecoder(json.JSONDecoder):
    def decode(self, obj, *args, **kwargs):
        if not kwargs.get('recurse', False):
            obj = super(JSONDecoder, self).decode(obj, *args, **kwargs)
        if isinstance(obj, list):
            for i in xrange(len(obj)):
                item = obj[i]
                if self._is_recursive(item):
                    obj[i] = self.decode(item, recurse=True)
        elif isinstance(obj, dict):
            if 'VACTemplaterDuration' in obj:
                return VACTemplaterDuration(*obj['VACTemplaterDuration'])
            if 'VACTemplaterACL' in obj:
                return VACTemplaterACL(*obj['VACTemplaterACL'])
            if 'datetime.datetime' in obj:
                return datetime.datetime(*obj['datetime.datetime'])
            elif 'datetime.date' in obj:
                return datetime.date(*obj['datetime.date'])
            elif 'datetime.time' in obj:
                return datetime.time(*obj['datetime.time'])
            elif 'decimal.Decimal' in obj:
                return decimal.Decimal(obj['decimal.Decimal'])
            else:
                for key, value in obj.items():
                    if self._is_recursive(value):
                        obj[key] = self.decode(value, recurse=True)
        return obj

    def _is_recursive(self, obj):
        return isinstance(obj, (list, dict))

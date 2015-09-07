# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import json
from django.db import models


class JSONField(models.Field):
    '''Simple JSON field.

        - https://github.com/bradjasper/django-jsonfield

    '''
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, basestring):
            try:
                return json.loads(value)
            except ValueError:
                pass
        return value

    def get_prep_value(self, value):
        if isinstance(value, basestring):
            return value
        if self.null and value is None:
            return None
        return json.dumps(value)

    def get_internal_type(self):
        return 'TextField'

# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.db import models
from django.utils.translation import ugettext_lazy as _
from vac_templater.models.base import JSONField

OID_MAX_LENGTH = 32


class Deployment(models.Model):
    user = models.ForeignKey(
        'User',
        null=True,
        on_delete=models.SET_NULL
    )

    group_name = models.CharField(
        _('group name'),
        null=False,
        blank=False,
        max_length=1024)

    group_oid = models.CharField(
        _('group OID'),
        null=False,
        blank=False,
        max_length=OID_MAX_LENGTH)

    branch_name = models.CharField(
        _('branch name'),
        null=False,
        blank=False,
        max_length=1024)

    branch_oid = models.CharField(
        _('branch OID'),
        null=False,
        blank=False,
        max_length=OID_MAX_LENGTH)

    old_head_oid = models.CharField(
        _('old head OID'),
        null=False,
        blank=False,
        max_length=OID_MAX_LENGTH)

    new_head_oid = models.CharField(
        _('new head OID'),
        null=False,
        blank=False,
        max_length=OID_MAX_LENGTH)

    vcl = models.TextField(
        _('VCL'),
        null=False,
        blank=False)

    message = models.TextField(
        _('message'),
        null=False,
        blank=False)

    changes = JSONField(
        _('changes'),
        null=False,
        blank=False)

    created_at = models.DateTimeField(
        _('created at'),
        null=False,
        auto_now_add=True)

    updated_at = models.DateTimeField(
        _('updated at'),
        null=False,
        auto_now=True)

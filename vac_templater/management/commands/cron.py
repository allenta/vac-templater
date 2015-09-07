# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = ('Task scheduler. Should be called by cron every minute.')

    def handle(self, *args, **options):
        Session.objects.filter(expire_date__lt=timezone.now()).delete()

# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.core.management.base import NoArgsCommand
from django.core.management import call_command


class Command(NoArgsCommand):
    help = 'Upgrades DB schema.'

    def handle_noargs(self, **options):
        call_command('migrate')
        call_command('createcachetable')

# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.core.management.base import BaseCommand
from vac_templater.runner import default_config


class Command(BaseCommand):
    help = 'Dumps sample configuration file.'

    def handle(self, *args, **options):
        self.stdout.write(default_config())

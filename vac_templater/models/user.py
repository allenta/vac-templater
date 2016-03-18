# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db import models
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, username, password=None):
        if not username:
            raise ValueError('The given username must be set')
        user = self.model(username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password):
        self.create_user(username, password)


class User(AbstractBaseUser):
    username = models.CharField(
        _('username'),
        null=False,
        max_length=256,
        primary_key=True)

    vac_cookie = models.CharField(
        _('VAC cookie'),
        null=True,
        blank=False,
        max_length=4096)

    last_validation = models.DateTimeField(
        _('last validation'),
        null=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ()

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def set_password(self, raw_password):
        # Don't store any password.
        self.set_unusable_password()

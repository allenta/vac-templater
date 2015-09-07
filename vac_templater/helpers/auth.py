# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import datetime
import logging
from django.utils import timezone
from vac_templater.helpers.vac import VAC
from vac_templater.models import User


REVALIDATION_FREQUENCY = 60


class VACBackend(object):
    '''Authenticate against the VAC with a login and password.

    '''
    def authenticate(self, username=None, password=None):
        # Authenticate against the VAC.
        vac = VAC()
        if vac.login(username, password):
            # Recover or build user instance.
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User(username=username)

            # Update VAC cookie info.
            user.vac_cookie = vac.cookie
            user.last_validation = timezone.now()
            user.save()

            # Done!
            return user
        return None

    def get_user(self, user_id):
        try:
            # Fetch user.
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            user = None
        else:
            # Does the user have a current session?
            if user.vac_cookie is None or user.last_validation is None:
                user = None

            # Is a revalidation needed?
            elif user.last_validation < (
                    timezone.now() -
                    datetime.timedelta(seconds=REVALIDATION_FREQUENCY)):
                # Check session against the VAC.
                try:
                    vac = VAC(user.vac_cookie)
                    if vac.validate_session():
                        # Update VAC cookie info.
                        user.last_validation = timezone.now()
                        user.save()
                    else:
                        # Session is no longer valid.
                        user.vac_cookie = None
                        user.save()
                        user = None

                # Problems revalidating. VAC unavailable? Log out user.
                except VAC.Exception as e:
                    user = None
                    logging.getLogger('vac-templater').exception(e)

        # Done!
        return user

    def has_perm(self, user_obj, perm, obj=None):
        return True

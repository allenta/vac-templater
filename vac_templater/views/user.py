# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import logging
import urlparse
from abc import ABCMeta
from django.contrib.auth.decorators import login_required
from django.contrib import auth, messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View
from vac_templater.helpers.vac import VAC
from vac_templater.helpers.views import ajaxify
from vac_templater.forms.user import LoginForm


class Base(View):
    __metaclass__ = ABCMeta

    @method_decorator(ajaxify)
    def dispatch(self, request, *args, **kwargs):
        return super(Base, self).dispatch(
            request, *args, **kwargs)


class Login(Base):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return super(Login, self).dispatch(
                request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('home'))

    def get(self, request):
        # Destination?
        destination = request.GET.get(
            auth.REDIRECT_FIELD_NAME, reverse('home'))

        # Don't allow redirection to a different host.
        netloc = urlparse.urlparse(destination)[1]
        if netloc and netloc != request.get_host():
            destination = reverse('home')

        # Done!
        form = LoginForm(initial={'destination': destination})
        return self._render(form)

    def post(self, request):
        form = LoginForm(data=request.POST)
        try:
            if form.is_valid():
                # Log user in.
                auth.login(request, form.user)

                # Done!
                messages.info(request, _('Welcome back!'))
                return HttpResponseRedirect(
                    form.cleaned_data.get('destination'))
            else:
                return self._render(form)

        # Failed VAC request.
        except VAC.Exception as e:
            logging.getLogger('vac-templater').exception(e)
            messages.error(request, _(
                'Failed to execute VAC request. Is the VAC running?'))
            return HttpResponseRedirect(reverse('user:login'))

    def _render(self, form):
        return {
            'template': 'vac-templater/user/login.html',
            'context': {
                'form': form,
            },
        }


class Logout(Base):
    @method_decorator(login_required)
    def get(self, request):
        try:
            # Logout from VAC.
            if request.user.vac_cookie is not None:
                VAC(request.user.vac_cookie).logout()
                request.user.vac_cookie = None
                request.user.save()

            # Logout locally.
            auth.logout(request)

            # Done!
            messages.success(request, _(
                'You have been disconnected. See you soon!'))
            return HttpResponseRedirect(reverse('home'))

        # Failed VAC request.
        except VAC.Exception as e:
            logging.getLogger('vac-templater').exception(e)
            messages.error(request, _(
                'Failed to execute VAC request. Is the VAC running?'))
            return HttpResponseRedirect(reverse('home'))

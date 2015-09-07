# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.views.generic import View
from vac_templater.helpers.views import ajaxify
from vac_templater.views.vcl import Deploy


class Index(View):
    @method_decorator(ajaxify)
    def get(self, request):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('home'))
        else:
            return HttpResponseRedirect(reverse('user:login'))


class Home(View):
    @method_decorator(ajaxify)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return Deploy.as_view()(request)

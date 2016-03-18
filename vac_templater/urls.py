# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.conf.urls import patterns, include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.defaults import (
    page_not_found, permission_denied, server_error)
from vac_templater.views import base as base_views
from vac_templater.views import vcl as vcl_views
from vac_templater.views import task as task_views
from vac_templater.views import user as user_views
from vac_templater.helpers import DEFAULT_ERROR_MESSAGE


###############################################################################
## '^vcl/' HANDLERS.
###############################################################################

vcl_patterns = patterns(
    '',
    url(r'^deploy/$',
        vcl_views.Deploy.as_view(),
        name='deploy'),
    url(r'^deployment/(?P<deployment_id>\d+)$',
        vcl_views.Deployment.as_view(),
        name='deployment'),
    url(r'^history/$',
        vcl_views.History.as_view(),
        name='history'),
)

###############################################################################
## '^user/' HANDLERS.
###############################################################################

user_patterns = patterns(
    '',
    url(r'^login/$',
        user_views.Login.as_view(),
        name='login'),
    url(r'^logout/$',
        user_views.Logout.as_view(),
        name='logout'),
)

###############################################################################
## '^task/' HANDLERS.
###############################################################################

task_patterns = patterns(
    '',
    url(r'^(?P<token>[0-9A-Za-z-:_]+)/progress/$',
        task_views.Progress.as_view(),
        name='progress'),
    url(r'^(?P<token>[0-9A-Za-z-:_]+)/cancel/$',
        task_views.Cancel.as_view(),
        name='cancel'),
    # url(r'^example/$',
    #     task_views.Example.as_view(),
    #     name='example'),
)

###############################################################################
## ALL URL HANDLERS.
###############################################################################

urlpatterns = i18n_patterns(
    '',
    url(r'^$',
        base_views.Index.as_view(),
        name='index'),
    url(r'^home/$',
        base_views.Home.as_view(),
        name='home'),
    url(r'^vcl/', include(vcl_patterns, namespace='vcl')),
    url(r'^user/', include(user_patterns, namespace='user')),
    url(r'^task/', include(task_patterns, namespace='task')),
)


###############################################################################
## CUSTOM 403, 404, etc. HANDLERS.
###############################################################################

def _handler(default_handler, message):
    def fn(request, *args, **kwargs):
        from django.conf import settings
        if request.path_info == '/' or \
           (settings.IS_PRODUCTION and
            request.path_info.startswith(settings.PRODUCTION_MEDIA_URL)) or \
           (not settings.IS_PRODUCTION and
                request.path_info.startswith(settings.DEV_MEDIA_URL)):
            # Standard 403/404/500 response.
            return default_handler(request, *args, **kwargs)
        else:
            # Message + 302.
            messages.error(request, message)
            if request.user.is_authenticated():
                return HttpResponseRedirect(reverse('home'))
            else:
                return HttpResponseRedirect(reverse('user:login'))
    return fn

handler403 = _handler(permission_denied, _(
    'We are sorry, but you are not authorized to see the requested '
    'contents.'))

handler404 = _handler(page_not_found, _(
    'We are sorry, but the requested content could not be found.'))

handler500 = _handler(server_error, DEFAULT_ERROR_MESSAGE)

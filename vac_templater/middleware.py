# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from vac_templater.helpers.http import HttpResponseAjax
from vac_templater.helpers.views import get_messages
from vac_templater.helpers import commands


class CustomizationsMiddleware(object):
    def process_request(self, request):
        # Initialize page id.
        request.page_id = None

        # Use HTTP_X_FORWARDED_FOR header as REMOTE_ADDR if present.
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
            # Take just the first one.
            request.META['REMOTE_ADDR'] = \
                request.META['HTTP_X_FORWARDED_FOR'].split(',')[0]

        # Add custom is_iframe_upload method.
        request.is_iframe_upload = lambda: \
            request.method == 'POST' and \
            '_iframe_upload' in request.POST

        # Redefine is_ajax method.
        request.is_ajax = lambda: \
            request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or \
            request.is_iframe_upload()

        # Done!
        return None

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.page_id = request.resolver_match.url_name
        if request.resolver_match.namespaces:
            request.page_id = \
                '-'.join(request.resolver_match.namespaces) + '-' + \
                request.page_id
        return None


class SSLRedirectMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not settings.HTTPS_ENABLED == request.is_secure():
            return self._redirect(request, settings.HTTPS_ENABLED)
        return None

    def _redirect(self, request, secure):
        protocol = secure and 'https' or 'http'
        url = '%s://%s%s' % (
            protocol, request.get_host(), request.get_full_path())
        if settings.DEBUG and request.method == 'POST':
            raise RuntimeError(
                '''Django can't perform a redirect while maintaining POST data.
                Please structure your views so that redirects only occur during
                GETs.''')
        if request.is_ajax():
            return HttpResponseAjax([commands.redirect(url)])
        else:
            return HttpResponseRedirect(url)


class MessagingMiddleware(object):
    def process_response(self, request, response):
        if isinstance(response, HttpResponseAjax):
            if not response.contains_redirection():
                messages = get_messages(request)
                if len(messages) > 0:
                    response.add_command(commands.notify(messages))
        return response


class VersionMiddleware(object):
    def process_response(self, request, response):
        if isinstance(response, HttpResponseAjax):
            response.add_command(commands.check_version())
        return response


class AjaxRedirectMiddleware(object):
    '''
    Intercepts standard HTTP redirections replacing them by AJAX commands when
    required.
    '''
    def process_response(self, request, response):
        if request.is_ajax():
            if isinstance(response, HttpResponseRedirect) or \
               isinstance(response, HttpResponsePermanentRedirect):
                return HttpResponseAjax([
                    commands.redirect(response['Location'])])
        return response

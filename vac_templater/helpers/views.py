# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib import messages
from vac_templater.helpers.http import HttpResponseAjax
from vac_templater.helpers.commands import set_content


def ajax_required(fn):
    def wrapped(request, *args, **kwargs):
        if request.is_ajax():
            return fn(request, *args, **kwargs)
        else:
            return HttpResponseBadRequest()
    return wrapped


def ajaxify(fn):
    def wrapped(request, *args, **kwargs):
        result = fn(request, *args, **kwargs)
        if isinstance(result, HttpResponse):
            return result
        else:
            if request.is_ajax():
                contents = render_to_string(
                    result['template'],
                    result['context'],
                    context_instance=RequestContext(request))
                return HttpResponseAjax([
                    set_content(contents),
                ], request)
            else:
                return render_to_response(
                    result['template'],
                    result['context'],
                    context_instance=RequestContext(request))
    return wrapped


def get_messages(request):
    return [{
        'type': (messages.constants.DEFAULT_TAGS[message.level]
                 if message.level in (messages.INFO, messages.SUCCESS,
                                      messages.WARNING, messages.ERROR)
                 else messages.constants.DEFAULT_TAGS[messages.INFO]),
        'message': unicode(message.message),
        'tags': message.tags,
    } for message in messages.get_messages(request)]

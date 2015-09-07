# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.contrib import messages
# from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View
from vac_templater import tasks
from vac_templater.helpers import DEFAULT_ERROR_MESSAGE, commands
from vac_templater.helpers.http import HttpResponseAjax
# from vac_templater.helpers.views import ajaxify


class Progress(View):
    def get(self, request, token):
        status = tasks.find(request, token)
        if status is not None:
            if status.is_completed():
                cmds = [commands.hide_progress()]
                if status.callback:
                    fn = status.callback['fn']
                    if isinstance(fn, tuple) and len(fn) == 2:
                        (path, static_method) = fn
                        index = path.rfind('.')
                        classname = path[index + 1:len(path)]
                        module = __import__(
                            path[0:index], fromlist=[classname])
                        klass = getattr(module, classname)
                        cmds.extend(getattr(klass, static_method).__call__(
                            request,
                            status.result,
                            status.callback['context']
                        ))
                status.forget()
                return HttpResponseAjax(cmds, request)
            elif status.is_failed():
                status.forget()
                messages.error(request, DEFAULT_ERROR_MESSAGE)
                return HttpResponseAjax([
                    commands.hide_progress(),
                ], request)
            elif status.is_cancelled():
                status.forget()
                return HttpResponseAjax([
                    commands.hide_progress(),
                ], request)
            elif status.is_running():
                return HttpResponseAjax([
                    commands.update_progress(status.progress),
                ], request)
            else:
                return HttpResponseAjax([
                    commands.update_progress(),
                ], request)
        else:
            messages.error(request, DEFAULT_ERROR_MESSAGE)
            return HttpResponseAjax([
                commands.hide_progress(),
            ], request)


class Cancel(View):
    def post(self, request, token):
        status = tasks.find(request, token)
        if status is not None:
            status.cancel()
            messages.info(request, _('The task execution has been aborted.'))
        else:
            messages.error(request, DEFAULT_ERROR_MESSAGE)
        return HttpResponseAjax([
            commands.hide_progress(),
        ], request)


# class Example(View):
#     @method_decorator(ajaxify)
#     def get(self, request):
#         import datetime
#         start_time = datetime.datetime.now()
#         token = tasks.enqueue(
#             request, tasks.ExampleTask, 123, 'blah',
#             callback={
#                 'fn': (
#                     'vac_templater.views.task.Example',
#                     'callback',
#                 ),
#                 'context': {
#                     'start_time': start_time,
#                 }
#             })
#         return HttpResponseAjax([
#             commands.show_progress(token),
#         ], request)
#
#     @classmethod
#     def callback(cls, request, result, context):
#         messages.success(
#             request,
#             'Example task done! Started at: %(time)s | Result: %(result)s' % {
#                 'time': context['start_time'],
#                 'result': result,
#             })
#         return []

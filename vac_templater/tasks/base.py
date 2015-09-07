# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import pickle
import sys
import traceback
import uuid
from django.utils import translation
from django.conf import settings
from django.core.cache import cache


class Task(object):
    TIMEOUT = 600

    def __init__(self, id):
        self._id = id

    @classmethod
    def delay(cls, *args, **kwargs):
        id = str(uuid.uuid4())
        kwargs['language'] = translation.get_language()
        import uwsgi
        uwsgi.spool({
            'task': pickle.dumps(cls(id)),
            'args': pickle.dumps(args),
            'kwargs': pickle.dumps(kwargs),
        })
        return TaskStatus(id)

    @classmethod
    def status(cls, id):
        return TaskStatus.find(id)

    def run(self, *args, **kwargs):
        # Extract & remove special 'language' argument.
        language = kwargs.pop('language', settings.LANGUAGE_CODE)

        # Extract & remove special 'callback' argument.
        callback = kwargs.pop('callback', None)

        # Switch language and execute task.
        try:
            with translation.override(language):
                status = TaskStatus.find(self._id)
                if status is not None and status.is_enqueued():
                    status.run()
                    result = self.irun(*args, **kwargs)
                    status = TaskStatus.find(self._id)
                    if status is not None and status.is_running():
                        status.complete(result, callback)
        except Exception as e:
            status = TaskStatus.find(self._id)
            if status is not None:
                status.fail()
            raise e

    def set_progress(self, count=0, total=100):
        status = TaskStatus.find(self._id)
        if status is not None and status.is_running():
            status.set_progress(
                int((float(min(count, total)) / float(total)) * 100))
        else:
            raise CancelledTaskException()

    def irun(self, *args, **kwargs):
        raise NotImplementedError('Please implement this method')


class TaskStatus(object):
    PREFIX = 'vac-templater:tasks:'

    ENQUEUED = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    CANCELLED = 5

    def __init__(self, id):
        self._id = id
        self._update(self.ENQUEUED, None)

    @classmethod
    def find(cls, id):
        return cache.get(cls.PREFIX + id)

    @property
    def id(self):
        return self._id

    @property
    def progress(self):
        assert self._status == self.RUNNING
        return self._data['progress']

    @property
    def result(self):
        assert self._status == self.COMPLETED
        return self._data['result']

    @property
    def callback(self):
        assert self._status == self.COMPLETED
        return self._data['callback']

    def is_enqueued(self):
        return self._status == self.ENQUEUED

    def is_running(self):
        return self._status == self.RUNNING

    def is_completed(self):
        return self._status == self.COMPLETED

    def is_failed(self):
        return self._status == self.FAILED

    def is_cancelled(self):
        return self._status == self.CANCELLED

    def run(self):
        assert self._status == self.ENQUEUED
        self._update(self.RUNNING, {'progress': 0})

    def complete(self, result, callback):
        assert self._status == self.RUNNING
        self._update(self.COMPLETED, {'result': result, 'callback': callback})

    def fail(self):
        assert self._status in (self.ENQUEUED, self.RUNNING)
        self._update(self.FAILED, None)

    def cancel(self):
        self._update(self.CANCELLED, None)

    def set_progress(self, value):
        assert self._status == self.RUNNING
        self._update(self.RUNNING, dict(self._data, progress=value))

    def forget(self):
        cache.delete(self.PREFIX + self._id)

    def _update(self, status, data):
        self._status = status
        self._data = data
        cache.set(self.PREFIX + self._id, self, Task.TIMEOUT)


class CancelledTaskException(Exception):
    pass


# class ExampleTask(Task):
#     def irun(self, a, b):
#         import time
#         from vac_templater.helpers.mail import send_templated_mail
#         try:
#             for i in range(1, 11):
#                 self.set_progress(i * 10, 100)
#                 time.sleep(1)
#             send_templated_mail(
#                 template_name='emails/vcl/deploy.email',
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 to=[admin[1] for admin in settings.ADMINS],
#                 bcc=settings.DEFAULT_BCC_EMAILS,
#                 context={},
#             )
#             return [a, b]
#         except CancelledTaskException:
#             return [None, None]


def spooler(env):
    import uwsgi
    try:
        task = pickle.loads(env['task'])
        task.run(*pickle.loads(env['args']), **pickle.loads(env['kwargs']))
    except:
        traceback.print_exc(file=sys.stderr)
    return uwsgi.SPOOL_OK

# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.core.signing import TimestampSigner, b64_encode, b64_decode
from vac_templater.tasks.base import Task
#from vac_templater.tasks.base import ExampleTask


def enqueue(request, task, *args, **kwargs):
    status = task.delay(*args, **kwargs)
    signer = TimestampSigner(key=request.session.session_key, sep=':')
    return signer.sign(b64_encode(status.id))


def find(request, token):
    try:
        signer = TimestampSigner(key=request.session.session_key, sep=':')
        id = b64_decode(signer.unsign(token, max_age=Task.TIMEOUT).encode('utf-8'))
        return Task.status(id)
    except:
        return None

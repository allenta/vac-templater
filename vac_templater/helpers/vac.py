# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import json
from contextlib import closing
from datetime import datetime
from requests import Session, Request
from requests.exceptions import RequestException
from django.conf import settings


def restricted(f):
    def wrapper(self, *args, **kwargs):
        if self.cookie is None:
            raise VAC.AuthenticationException(
                'Failed to execute VAC request: user is not authenticated.')
        return f(self, *args, **kwargs)
    return wrapper


class VAC(object):
    COOKIE_NAME = 'JSESSIONID'
    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
    DEFAULT_TIMEOUT = 5  # Seconds.

    class Exception(Exception):
        pass

    class AuthenticationException(Exception):
        pass

    class CacheGroup(object):
        def __init__(self, spec):
            self.id = spec['_id']['$oid']
            self.name = spec['name']
            self.active_vcl = \
                spec['activeVCL']['$id']['$oid'] \
                if 'activeVCL' in spec else None
            self.created_at = datetime.strptime(
                spec['created']['$date'], VAC.DATETIME_FORMAT)
            self.updated_at = datetime.strptime(
                spec['timestamp']['$date'], VAC.DATETIME_FORMAT)

    class VCL(object):
        def __init__(self, spec):
            self.id = spec['_id']['$oid']
            self.name = spec['name']
            self.user = spec['createdByUser']['$id']['$oid']
            self.created_at = datetime.strptime(
                spec['created']['$date'], VAC.DATETIME_FORMAT)
            self.updated_at = datetime.strptime(
                spec['timestamp']['$date'], VAC.DATETIME_FORMAT)

    class VCLCommit(object):
        def __init__(self, spec):
            self.id = spec['_id']['$oid']
            self.branch = spec['branch']['$id']['$oid']
            self.content = spec['content']
            self.is_head = spec['head']
            self.user = spec['committedByUser']['$id']['$oid']
            self.created_at = datetime.strptime(
                spec['created']['$date'], VAC.DATETIME_FORMAT)
            self.updated_at = datetime.strptime(
                spec['timestamp']['$date'], VAC.DATETIME_FORMAT)

    def __init__(self, cookie=None):
        self.cookie = cookie
        self._local_cache = {}

    def flush_local_cache(self):
        '''Clean up the local cache.

        Responses to GET requests are stored in a local cache to minimize the
        requests sent to the VAC. Whenever a successful login or logout
        operation is done this method is automatically called.
        '''
        self._local_cache = {}

    def login(self, username, password):
        '''Try to start a new authenticated session.'''
        if self.cookie is None:
            response = self._execute('POST', '/api/rest/login', data={
                'username': username,
                'password': password,
            })
            if response.status_code == 200 and \
               self.COOKIE_NAME in response.cookies:
                self.cookie = response.cookies[self.COOKIE_NAME]
                self.flush_local_cache()
        return self.cookie is not None

    def logout(self):
        '''Close the current session.'''
        if self.cookie is not None:
            self._execute('POST', '/api/rest/logout', codes=[200])
            self.cookie = None
            self.flush_local_cache()

    def validate_session(self):
        '''Check the current session is still valid.'''
        if self.cookie is not None:
            response = self._execute('POST', '/api/rest/checkcookie')
            return response.status_code == 200
        return False

    @restricted
    def groups(self):
        '''Get the list of groups.'''
        response = self._execute('GET', '/api/v1/group', codes=[200])
        return map(VAC.CacheGroup, json.loads(response.text)['list'])

    @restricted
    def group(self, group_id):
        '''Get a group by its id.'''
        response = self._execute(
            'GET', '/api/v1/group/%(group_id)s' % {
                'group_id': group_id,
            }, codes=[200, 404])
        if response.status_code == 200:
            return VAC.CacheGroup(json.loads(response.text))
        else:
            return None

    @restricted
    def vcl(self, vcl_id):
        '''Get a VCL (branch) by its id.'''
        response = self._execute(
            'GET', '/api/v1/vcl/%(vcl_id)s' % {
                'vcl_id': vcl_id,
            }, codes=[200, 404])
        if response.status_code == 200:
            return VAC.VCL(json.loads(response.text))
        else:
            return None

    @restricted
    def vcl_head(self, vcl_id):
        '''Get the current head (VCL commit) of a given VCL (branch).'''
        response = self._execute(
            'GET', '/api/v1/vcl/%(vcl_id)s/head' % {
                'vcl_id': vcl_id,
            }, codes=[200, 404])
        if response.status_code == 200:
            return VAC.VCLCommit(json.loads(response.text))
        else:
            return None

    @restricted
    def vcl_push(self, vcl_id, vcl_content, group_id=None):
        '''Push a new VCL commit to a given VCL (branch).'''
        response = self._execute(
            'POST', '/api/v1/vcl/%(vcl_id)s/push' % {
                'vcl_id': vcl_id,
            },
            codes=[200, 400],
            data=vcl_content,
            headers={'Content-Type': 'text/plain'})
        success = (response.status_code == 200)

        # Optional: try to force group to reload the current head of the
        # VCL branch immediately.
        if success and group_id:
            self._execute(
                'PUT', '/api/v1/group/%(group_id)s/vcl/%(vcl_id)s/deploy' % {
                    'group_id': group_id,
                    'vcl_id': vcl_id,
                },
                codes=[200, 204])

        parsed_response = json.loads(response.text)
        return {
            'success': success,
            'message': parsed_response['message'],
            'vcl': VAC.VCLCommit(parsed_response),
        }

    def _execute(self, method, path, codes=None, **request_kwargs):
        try:
            request = Request(
                method, settings.VAC_API + path, **request_kwargs)
            with closing(Session()) as session:
                # Add session cookie if user is authenticated.
                if self.cookie is not None:
                    session.cookies[self.COOKIE_NAME] = self.cookie

                response = None

                # Try with local cache if this is a GET request.
                if method == 'GET':
                    response = self._local_cache.get(path)

                # No cached response? Send request.
                if response is None:
                    response = session.send(
                        session.prepare_request(request),
                        stream=False,
                        timeout=self.DEFAULT_TIMEOUT)

                    # Store response in the local cache if this is a GET
                    # request.
                    if method == 'GET':
                        self._local_cache[path] = response

                # Check response status code is in the list of valid codes
                # if any was supplied.
                if codes is not None and response.status_code not in codes:
                    # Unauthorized: raise a VAC.AuthenticationException.
                    if response.status_code == 401:
                        raise VAC.AuthenticationException(
                            'Failed to execute VAC request [%(path)s]: user '
                            'is not authenticated.' % {
                                'path': path,
                            }
                        )

                    # Other unexpected codes: raise a VAC.Exception.
                    else:
                        raise VAC.Exception(
                            'Unexpected VAC response code (%(code)d) '
                            '[%(path)s]:\n%(text)s' % {
                                'code': response.status_code,
                                'path': path,
                                'text': response.text,
                            }
                        )

                # Done!
                return response

        # Unexpected error communicating with the VAC: raise a VAC.Exception.
        except RequestException as e:
            raise VAC.Exception(
                'Failed to execute VAC request [%(path)s]:\n%(message)s' % {
                    'path': path,
                    'message': e.message,
                }
            )

#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import, print_function
import json
import sys
from contextlib import closing
from tabulate import tabulate
from requests import Session, Request
from requests.exceptions import RequestException
from argparse import ArgumentParser

VAC_LOCATION = 'http://127.0.0.1:8000'
VAC_USER = 'vac'
VAC_PASSWORD = 'vac'
VAC_TIMEOUT = 10


###############################################################################
## CACHE GROUPS
###############################################################################

def _cache_groups(vac, options):
    # Fetch groups.
    groups = json.loads(vac.get('/api/v1/group', codes=[200]).text)['list']

    # Build result.
    headers = ['ID', 'NAME', 'DESCRIPTION']
    rows = []
    for group in groups:
        rows.append([
            group['_id']['$oid'],
            _summarize(group.get('name', '-'), 32),
            _summarize(group.get('description', '-'), 32),
        ])

    # Done!
    print(tabulate(rows, headers=headers, tablefmt='psql'))


###############################################################################
## VCL BRANCHES
###############################################################################

def _vcl_branches(vac, options):
    # Fetch branches.
    branches = json.loads(vac.get('/api/v1/vcl', codes=[200]).text)['list']

    # Build result.
    headers = ['ID', 'NAME', 'DESCRIPTION']
    rows = []
    for branch in branches:
        rows.append([
            branch['_id']['$oid'],
            _summarize(branch.get('name', '-'), 32),
            _summarize(branch.get('description', '-'), 32),
        ])

    # Done!
    print(tabulate(rows, headers=headers, tablefmt='psql'))


###############################################################################
## DEPLOY
###############################################################################

def _deploy(vac, options):
    # Initializations.
    with open(options.file, 'r') as file:
        code = file.read()
    old_head = None
    rollback = False
    message = None

    # Fetch HEAD commit OID.
    response = vac.get('/api/v1/vcl/%s/head' % options.branch, codes=[200, 204])
    if response.status_code == 200:
        old_head = json.loads(response.text)['_id']['$oid']

    # Push new commit to the VCL branch.
    response = vac.post(
        '/api/v1/vcl/%s/push' % options.branch,
        headers={'Content-Type': 'application/json'},
        data=json.dumps({'content': code}),
        codes=None)

    # Deploy pushed commit to cache group?
    if response.status_code == 200:
        new_head = json.loads(response.text)['_id']['$oid']
        response = vac.put(
            '/api/v1/group/%s/vcl/%s/deploy' % (
                options.group,
                options.branch,
            ),
            codes=None)
        if response.status_code == 200:
            print('VCL commit %(commit)s successfully deployed.' % {
                'commit': new_head,
            })
        else:
            rollback = True
    else:
        rollback = True
        if response.text:
            message = json.loads(response.text).get('message')

    # Rollback to previous HEAD?
    if rollback:
        if old_head is not None:
            response = vac.post(
                '/api/v1/vcl/%s/push/%s' % (
                    options.branch,
                    old_head,
                ),
                codes=None)

        print('Failed to deploy! Rolled back to VCL commit %(commit)s.' % {
            'commit': old_head,
        }, file=sys.stderr)
        if message is not None:
            print('\n%(message)s' % {
                'message': message,
            }, file=sys.stderr)


###############################################################################
## HELPERS
###############################################################################

class VAC(object):
    def get(self, path, headers=None, codes=None):
        return self._execute(
            Request('GET', VAC_LOCATION + path, headers=headers),
            path,
            codes)

    def post(self, path, headers=None, data=None, codes=None):
        return self._execute(
            Request('POST', VAC_LOCATION + path, headers=headers, data=data),
            path,
            codes)

    def put(self, path, headers=None, codes=None):
        return self._execute(
            Request('PUT', VAC_LOCATION + path, headers=headers),
            path,
            codes)

    def _execute(self, request, path, codes):
        try:
            with closing(Session()) as session:
                session.auth = (VAC_USER, VAC_PASSWORD)
                response = session.send(
                    session.prepare_request(request),
                    stream=False,
                    timeout=VAC_TIMEOUT)
                assert \
                    codes is None or response.status_code in codes, \
                    'Unexpected VAC response code (%(code)d): %(path)s' % {
                        'code': response.status_code,
                        'path': path,
                    }
                return response
        except RequestException as e:
            raise Exception('Failed to execute VAC request (%(message)s): %(path)s' % {
                'message': e.message,
                'path': path,
            })


def _summarize(value, max_length):
    result = value.replace('\n', ' ').replace('\r', '')
    if len(result) > max_length:
        result = result[:max_length] + '...'
    return result


###############################################################################
## MAIN
###############################################################################

def main():
    # Base parser.
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    # 'cache-groups' command.
    subparser = subparsers.add_parser(
        'cache-groups',
        help='list available VAC cache groups')

    # 'vcl-branches' command.
    subparser = subparsers.add_parser(
        'vcl-branches',
        help='list available VAC VCL branches')

    # 'deploy' command.
    subparser = subparsers.add_parser(
        'deploy',
        help='deploy single VCL file to an existing VCL branch & cache group')
    subparser.add_argument(
        'group',
        help='VAC cache group OID')
    subparser.add_argument(
        'branch',
        help='VAC VCL branch OID')
    subparser.add_argument(
        'file',
        help='VCL file')

    # Parse arguments & execute command.
    options = parser.parse_args()
    vac = VAC()
    globals()['_' + options.command.replace('-', '_').replace('.', '_')](vac, options)


if __name__ == '__main__':
    main()

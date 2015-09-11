# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import logging
from abc import ABCMeta
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from vac_templater import tasks
from vac_templater.tasks.vac import PushVCLTask
from vac_templater.forms.vcl import CacheGroupForm, DeployForm, HistoryForm
from vac_templater.helpers import commands
from vac_templater.helpers.http import HttpResponseAjax
from vac_templater.helpers.vac import VAC
from vac_templater.helpers.views import ajaxify
from vac_templater import models


class Base(View):
    __metaclass__ = ABCMeta

    @method_decorator(login_required)
    @method_decorator(ajaxify)
    def dispatch(self, *args, **kwargs):
        return super(Base, self).dispatch(*args, **kwargs)


class Deploy(Base):
    def get(self, request):
        return self._process(request)

    def post(self, request):
        return self._process(request)

    def _process(self, request):
        cache_group_form = None
        deploy_form = None

        try:
            vac = VAC(request.user.vac_cookie)

            # Cache group selected?
            cache_group_form = CacheGroupForm(
                vac, prefix='cache-group', data=request.POST or None)
            if cache_group_form.is_bound and cache_group_form.is_valid():
                # Deploying?
                deploying = (request.POST.get('op') == 'deploy')
                deploy_form = DeployForm(
                    vac,
                    cache_group_form.cleaned_data['group'],
                    request.user,
                    prefix='settings',
                    data=request.POST if deploying else None)
                if deploy_form.is_bound:
                    if deploy_form.is_valid():
                        deploy_form.execute()
                        token = tasks.enqueue(
                            request,
                            PushVCLTask,
                            request.user.username,
                            deploy_form.group.id,
                            deploy_form.vcl_commit.id,
                            deploy_form.new_vcl,
                            deploy_form.changes,
                            callback={
                                'fn': (
                                    'vac_templater.views.vcl.Deploy',
                                    'callback',
                                ),
                                'context': {},
                            })

                        return HttpResponseAjax([
                            commands.show_progress(token),
                        ], request)
                    else:
                        if deploy_form.non_field_errors():
                            for error in deploy_form.non_field_errors():
                                messages.error(request, error)
                        else:
                            messages.error(
                                request,
                                _('There are some errors in the values you '
                                  'supplied. Please, fix them and try again.'))

        # Unauthenticated VAC request.
        except VAC.AuthenticationException:
            messages.error(request, _(
                'Your session has automatically expired. Please, log in '
                'again.'))

            # Clear VAC cookie info.
            request.user.vac_cookie = None
            request.user.save()

            # Logout locally.
            auth.logout(request)
            return HttpResponseRedirect(reverse('home'))

        # Failed VAC request.
        except VAC.Exception as e:
            logging.getLogger('vac-templater').exception(e)
            messages.error(request, _(
                'Failed to connect to the VAC. Is it running? Do you have r/w '
                'access to it?'))

        return {
            'template': 'vac-templater/vcl/deploy.html',
            'context': {
                'cache_group_form': cache_group_form,
                'deploy_form': deploy_form,
            },
        }

    @classmethod
    def callback(cls, request, result, context):
        if result['deployment_id']:
            deployment = models.Deployment.objects.get(
                pk=result['deployment_id'])
            messages.success(
                request,
                _('The VCL has been safely deployed to group %s') % (
                    deployment.group_name))
            return [
                commands.redirect(
                    reverse(
                        'vcl:deployment',
                        kwargs={
                            'deployment_id': deployment.id,
                        }
                    )
                ),
            ]
        else:
            messages.error(request, result['error'])
            return [commands.redirect(reverse('vcl:deploy'))]


class Deployment(Base):
    def get(self, request, deployment_id):
        deployment = models.Deployment.objects.get(pk=deployment_id)
        return {
            'template': 'vac-templater/vcl/deployment.html',
            'context': {
                'deployment': deployment,
            },
        }


class History(Base):
    def get(self, request):
        form = HistoryForm(data=request.GET)
        if form.is_valid():
            form.execute()
            return {
                'template': 'vac-templater/vcl/history.html',
                'context': {
                    'form': form,
                },
            }
        else:
            raise SuspiciousOperation()

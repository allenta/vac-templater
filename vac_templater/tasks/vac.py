# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import logging
from django.conf import settings
from django.utils.translation import ugettext as _
from vac_templater.helpers.mail import send_templated_mail
from vac_templater.helpers.vac import VAC
from vac_templater.models import User, Deployment
from vac_templater.tasks.base import Task


class PushVCLTask(Task):
    def irun(self, username, group_id, vcl_commit_id, vcl_content, changes):
        deployment = None
        error = None

        try:
            try:
                user = User.objects.get(pk=username)
            except User.DoesNotExist:
                error = _('Error retrieving the current user. Reconnect and '
                          'try again.')
            else:
                if user.vac_cookie:
                    try:
                        vac = VAC(user.vac_cookie)
                        group = vac.group(group_id)
                        if group:
                            vcl = vac.vcl(group.active_vcl)
                            if vcl:
                                vcl_commit = vac.vcl_head(vcl.id)
                                if vcl_commit:
                                    if vcl_commit.id == vcl_commit_id:
                                        # Push VCL.
                                        result = vac.vcl_push(
                                            vcl.id,
                                            vcl_content,
                                            group.id,
                                            vcl_commit_id)

                                        if result['success']:
                                            # Keep track of this deployment.
                                            deployment = Deployment(
                                                user=user,
                                                group_name=group.name,
                                                group_oid=group.id,
                                                branch_name=vcl.name,
                                                branch_oid=vcl.id,
                                                old_head_oid=vcl_commit.id,
                                                new_head_oid=result['vcl'].id,
                                                vcl=result['vcl'].content,
                                                message=result['message'],
                                                changes=changes)
                                            deployment.save()

                                            # Notify by e-mail.
                                            send_templated_mail(
                                                template_name='emails/vcl/deploy.email',
                                                from_email=settings.DEFAULT_FROM_EMAIL,
                                                to=[admin[1] for admin in settings.ADMINS],
                                                bcc=settings.DEFAULT_BCC_EMAILS,
                                                context={
                                                    'base_url': settings.BASE_URL,
                                                    'deployment': deployment,
                                                },
                                            )
                                        else:
                                            error = result['message']
                                    else:
                                        error = _(
                                            'The VCL has been modified while '
                                            'you were updating it! Please, '
                                            'redo all required changes and '
                                            'try again.')
                                else:
                                    error = _(
                                        'The VCL has been undeployed from '
                                        'this group while you were updating '
                                        'it! No changes have been made.')
                            else:
                                error = _(
                                    'The VCL has been undeployed from this '
                                    'group while you were updating it! No '
                                    'changes have been made.')
                        else:
                            error = _('The selected group no longer exists.')

                    except VAC.AuthenticationException:
                        error = _('Your session in the VAC has been '
                                  'automatically expired. Reconnect and try'
                                  'again.')

                    except VAC.Exception as e:
                        logging.getLogger('vac-templater').exception(e)
                        error = _('Failed to connect to the VAC. Is it '
                                  'running? Do yo have r/w access to it?')
                else:
                    error = _('You must be authenticated to the VAC. '
                              'Reconnect and try again.')

        except Exception as e:
            error = 'Exception: %s' % e

        return {
            'deployment_id': deployment.id if deployment else None,
            'error': error,
        }

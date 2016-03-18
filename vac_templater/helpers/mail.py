# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.core.mail import EmailMultiAlternatives
from django.template import Context
from django.template.loader import get_template
from django.template.loader_tags import BlockNode, ExtendsNode


def send_templated_mail(template_name, from_email, to, bcc, context):
    template = get_template(template_name).template
    render_context = Context(context, autoescape=False)
    with render_context.bind_template(template):
        email = EmailMultiAlternatives(
            _get_node(template, render_context, 'subject'),
            _get_node(template, render_context, 'plain'),
            from_email=from_email,
            to=to,
            bcc=bcc)
        email.attach_alternative(
            _get_node(template, render_context, 'html'), 'text/html')
        email.send()


def _get_node(template, context, name, block_lookups=None):
    if block_lookups is None:
        block_lookups = {}
    for node in template.nodelist:
        if isinstance(node, BlockNode) and node.name == name:
            for i, n in enumerate(node.nodelist):
                if isinstance(n, BlockNode) and n.name in block_lookups:
                    node.nodelist[i] = block_lookups[n.name]
            return node.render(context)
        elif isinstance(node, ExtendsNode):
            return _get_node(
                node.get_parent(context),
                context,
                name,
                dict(node.blocks, **block_lookups))
    raise BlockNotFound("Node '%s' could not be found in template." % name)


class BlockNotFound(Exception):
    pass

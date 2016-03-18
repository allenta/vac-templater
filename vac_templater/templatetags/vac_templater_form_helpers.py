# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import re
from django import template
from django.forms.forms import BoundField

register = template.Library()

###############################################################################


@register.simple_tag
def form_errors(form):
    result = ''
    for error in form.non_field_errors():
        result += (
            '<div class="alert bg-danger text-danger">'
            '<a class="close" data-dismiss="alert">&times;</a>%s'
            '</div>') % error
    return result


###############################################################################


@register.tag
def form_group(parser, token):
    '''Return a div to enclose a form field (or several related form fields).

    Parameters:
        - Field or fields that will be enclosed by this div.
        - Any variables to be resolved in the context and that will be added as
          HTML classes for the div.
        - A single string with comma-separated classes that should also be
          added to the div.

    Two extra classes will be added to the div taking into account the fields
    provided:
        - has-error: if any of the fields has errors.
        - required: if any of the fields is required.

    Usage:
        {% form_group field1 field2 variable "class1 class2" %}
            ...
            {{ field1 }}
            {{ field2 }}
            ...
        {% endform_group %}

    Results in, for example:

        <div class="form-group value_for_variable class1 class2">
            ...
        </div>

    Or:

        <div class="form-group value_for_variable has-error required class1 class2">
            ...
        </div>
    '''
    nodelist = parser.parse(('endform_group',))
    parser.delete_first_token()
    p = re.compile(
        r'''^form_group (?P<variables>[^"']+)?(?:["'](?P<classes>[^"']*)["'])?$''')
    m = p.search(token.contents)
    variables = (m.group('variables') or '').strip().split(' ')
    classes = (m.group('classes') or '').strip().split(' ')
    return CaptureNode(nodelist, variables, classes)


class CaptureNode(template.Node):
    def __init__(self, nodelist, variables, classes):
        self.nodelist = nodelist
        self.variables = [template.Variable(var) for var in variables]
        self.classes = classes

    def render(self, context):
        classes = ['form-group']

        error = False
        required = False
        for variable in self.variables:
            value = variable.resolve(context)
            if isinstance(value, BoundField):
                error = error or len(value.errors) > 0
                required = required or value.field.required
            else:
                classes.append(str(value))

        if error:
            classes.append('has-error')
        if required:
            classes.append('required')

        classes += self.classes

        return '<div class="%(classes)s">%(content)s</div>' % {
            'classes': ' '.join(classes),
            'content': self.nodelist.render(context),
        }


###############################################################################


@register.simple_tag
def field_label(field):
    return (
        '<label for="%s" class="control-label">'
        '%s'
        '</label>') % (field.id_for_label, field.label)


@register.simple_tag
def field_help(field):
    if field.help_text:
        return '<span class="help-block">%s</span>' % field.help_text
    else:
        return ''


@register.simple_tag
def field_errors(field):
    result = ''
    for error in field.errors:
        result += (
            '<span class="help-block">'
            '<strong>%s</strong>'
            '</span>') % error
    return result

# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.core import validators
from django.forms import IntegerField, CharField, BooleanField, MultiValueField
from django.forms import MultiWidget
from django.utils.safestring import mark_safe


class FallbackMixinField(object):
    def __init__(self, default=None, choices=None, *args, **kwargs):
        # Fallback fields are never required. Trying to require them should be
        # an error.
        kwargs.setdefault('required', False)
        assert not kwargs['required'], 'No fallback field can be set as ' \
            'required.'

        # Set default value and choices.
        assert default is not None or choices, 'All fallback fields should ' \
            'provide a default value or/and a non-empty choices list.'
        self.default = choices[0] if default is None else default
        self.choices = choices

        # Done!
        super(FallbackMixinField, self).__init__(*args, **kwargs)

    def clean(self, value):
        value = super(FallbackMixinField, self).clean(value)
        if value in validators.EMPTY_VALUES or\
           (self.choices is not None and value not in self.choices):
            value = self.default
        return value


class FallbackIntegerField(FallbackMixinField, IntegerField):
    pass


class FallbackCharField(FallbackMixinField, CharField):
    pass


class FallbackBooleanField(FallbackMixinField, BooleanField):
    pass


class SortDirectionField(FallbackCharField):
    def __init__(self, *args, **kwargs):
        assert 'choices' not in kwargs, 'No custom choices can be set for a ' \
            'SortDirectionField'
        kwargs['choices'] = ['asc', 'desc']
        super(SortDirectionField, self).__init__(*args, **kwargs)


class RepeatableField(MultiValueField):
    '''Field that collects a list of values, all of them of the same kind.

    By passing a reference field to its initializer, the RepeatableField will
    take charge of creating enough copies of it to cover all initial values
    and still let room for another empty field that can be used to add an
    extra value to the list.

    As any MultiValueField, fields will have names like "name_0", with
    increasing numbers. Extra fields may be created using JS by cloning any
    pre-existent field and following this naming convention.
    '''
    class Widget(MultiWidget):
        def __init__(self, reference_field, *args, **kwargs):
            self.reference_field = reference_field
            super(RepeatableField.Widget, self).__init__(*args, **kwargs)

        def render(self, *args, **kwargs):
            return mark_safe(
                '<div class="repeatable-field">%s</div>' % super(
                    RepeatableField.Widget, self).render(*args, **kwargs))

        def value_from_datadict(self, data, files, name):
            # Rebuild widgets to adapt to the number of values that have been
            # sent (it could have changed if new fields were created with JS).
            self.widgets = [self.reference_field.widget] * len(
                [key for key in data.keys() if key.startswith(name + '_')])
            return super(RepeatableField.Widget, self).value_from_datadict(
                data, files, name)

        def decompress(self, value):
            # Make sure there's a value for every current widget.
            if value:
                return value + [u''] * (len(self.widgets) - len(value))
            return [u''] * len(self.widgets)

    def __init__(self, reference_field, *args, **kwargs):
        self.reference_field = reference_field
        kwargs['initial'] = kwargs.get('initial') or []
        # Build enough fields to cover the initial values plus one for allowing
        # a new value to be added.
        fields = [reference_field] * (len(kwargs['initial']) + 1)
        super(RepeatableField, self).__init__(
            fields=fields,
            require_all_fields=False,
            widget=RepeatableField.Widget(
                reference_field=reference_field,
                widgets=[field.widget for field in fields]
            ),
            *args, **kwargs)

    def clean(self, value):
        if isinstance(value, (list, tuple)):
            # Rebuild fields to adapt to the number of values that have been
            # sent (it could have been changed if new fields were created with
            # JS).
            self.fields = [self.reference_field] * len(value)
        return super(RepeatableField, self).clean(value)

    def compress(self, data_list):
        # Ignore empty values.
        return [value for value in data_list if value]

    def has_changed(self, initial, data):
        # Take into account the case when the number of subfields has changed.
        initial = self.widget.decompress(initial)
        return \
            (isinstance(initial, list) and
             isinstance(data, list) and
             len(initial) != len(data)) or \
            super(RepeatableField, self).has_changed(initial, data)

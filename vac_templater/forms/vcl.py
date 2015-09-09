# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from vac_templater.forms.base import FallbackIntegerField, FallbackCharField
from vac_templater.forms.base import SortDirectionField, RepeatableField
from vac_templater.helpers.vac_templater_config import (
    VACTemplaterConfig, VACTemplaterUser, VACTemplaterTextSetting,
    VACTemplaterLongTextSetting, VACTemplaterIntegerSetting,
    VACTemplaterDurationSetting, VACTemplaterDuration,
    VACTemplaterBooleanSetting, VACTemplaterACLSetting, VACTemplaterACL,
    VACTemplaterSelectSetting, VACTemplaterGroupSetting)
from vac_templater.helpers.paginator import Paginator
from vac_templater.models import Deployment


class CacheGroupForm(forms.Form):
    def __init__(self, vac, *args, **kwargs):
        super(CacheGroupForm, self).__init__(*args, **kwargs)

        # Dynamic cache group field.
        self._groups = vac.groups()
        self.fields['group'] = forms.ChoiceField(
            choices=[(group.id, group.name) for group in self._groups],
            error_messages={
                'invalid_choice': _('The selected group no longer exists.'),
            },
        )

    def clean_group(self):
        return next(
            group for group in self._groups
            if group.id == self.cleaned_data['group'])


class ACLField(forms.MultiValueField):
    class Widget(forms.MultiWidget):
        def decompress(self, value):
            if value:
                return [value.acls]
            return [[]]

    def __init__(self, *args, **kwargs):
        field = RepeatableField(
            forms.CharField(required=False),
            initial=kwargs['initial'].acls if 'initial' in kwargs else [])
        super(ACLField, self).__init__(
            fields=(
                field,
            ),
            require_all_fields=False,
            widget=ACLField.Widget(widgets=(
                field.widget,
            )),
            *args, **kwargs)

    def compress(self, data_list):
        return VACTemplaterACL(data_list[0])


class DurationField(forms.MultiValueField):
    class Widget(forms.MultiWidget):
        def decompress(self, value):
            if value:
                return [value.amount, value.granularity]
            return [None, None]

    def __init__(self, *args, **kwargs):
        amount_field = forms.FloatField(
            required=True, min_value=0, localize=True)
        granularity_field = forms.ChoiceField(required=True, choices=[
            (granularity, VACTemplaterDurationSetting.GRANULARITIES[granularity]['label'])
            for granularity in sorted(
                VACTemplaterDurationSetting.GRANULARITIES.keys(),
                key=lambda granularity: VACTemplaterDurationSetting.GRANULARITIES[granularity]['ms'])])
        super(DurationField, self).__init__(
            fields=(
                amount_field,
                granularity_field,
            ),
            require_all_fields=False,
            widget=DurationField.Widget(widgets=(
                amount_field.widget,
                granularity_field.widget,
            )),
            *args, **kwargs)

    def compress(self, data_list):
        return VACTemplaterDuration(data_list[0], data_list[1])


class DeployForm(forms.Form):
    FIELD_MAPPING = {
        VACTemplaterTextSetting: forms.CharField,
        VACTemplaterLongTextSetting: forms.CharField,
        VACTemplaterIntegerSetting: forms.IntegerField,
        VACTemplaterDurationSetting: DurationField,
        VACTemplaterBooleanSetting: forms.BooleanField,
        VACTemplaterACLSetting: ACLField,
        VACTemplaterSelectSetting: forms.ChoiceField,
    }

    def __init__(self, vac, group, user, *args, **kwargs):
        super(DeployForm, self).__init__(*args, **kwargs)

        # Extract parameters.
        self.vac = vac
        self.group = group
        self.vac_templater_user = VACTemplaterUser(user.username)

        # Initialize helper data.
        self.vcl_commit = None
        self.config = None
        self.config_errors = []
        self.fieldsets = {}
        self.changes = []

        # Result state. This will hold the result of the execution.
        self.new_vcl = None

        # Retrieve current VCL.
        if group.active_vcl:
            self.vcl_commit = vac.vcl_head(group.active_vcl)
            if self.vcl_commit:
                # Keep track of the current VCLCommit id in a hidden field to
                # make sure it doesn't change while filling the form.
                self.fields['vcl_commit_id'] = forms.CharField(
                    initial=self.vcl_commit.id,
                    widget=forms.HiddenInput)

                try:
                    # Parse VAC Templater config.
                    self.config = VACTemplaterConfig.parse(self.vcl_commit.content)
                except VACTemplaterConfig.ConfigError as e:
                    self.config_errors = e.messages
                else:
                    # Apply roles to current user if defined in the VCL.
                    self.vac_templater_user = next(
                        (vac_templater_user for vac_templater_user in self.config.users
                         if vac_templater_user.id == user.username),
                        self.vac_templater_user)

                    # Build all dynamic settings fields.
                    for setting in self.config.settings:
                        self._add_setting(setting)

    def clean(self):
        # Check VCL is still loaded.
        if self.vcl_commit:
            cleaned_data = super(DeployForm, self).clean()
            # Check VCL hasn't changed while filling the form.
            if self.vcl_commit.id == cleaned_data.get('vcl_commit_id'):
                # Validate values supplied for all settings.
                for setting in self.config.settings:
                    self._clean_setting(setting, cleaned_data)
            else:
                raise forms.ValidationError(_(
                    'The VCL has been modified while you were updating it! '
                    'Please, reload the page, redo all required changes and '
                    'try again.'), code='vcl-missmatch')
        else:
            raise forms.ValidationError(_(
                'The VCL has been undeployed from this group while you were '
                'updating it! No changes have been made.'), code='no-vcl')

    def execute(self):
        # Build new VCL.
        self.new_vcl = self.config.substitute(
            self.cleaned_data, self.vcl_commit.content)

    def _add_setting(self, setting):
        if type(setting) == VACTemplaterGroupSetting:
            # Add all subsettings.
            for subsetting in setting.settings:
                self._add_setting(subsetting)

            # If a field (or fieldset) for any subsetting has been created,
            # add this fieldset to the list. Otherwise, it shouldn't be taken
            # into acount because the user has nothing to edit on it.
            if any(subsetting for subsetting in setting.settings
                   if (subsetting.id in self.fields or
                       subsetting.id in self.fieldsets)):
                self.fieldsets[setting.id] = {
                    'legend': setting.name,
                    'description': setting.description,
                    'subsettings': setting.settings,
                }
        else:
            if setting.role in self.vac_templater_user.roles:
                field_cls = DeployForm.FIELD_MAPPING[type(setting)]
                field_attrs = {
                    'label': setting.name,
                    'required': False,
                    'initial': self.config.parse_value(
                        self.vcl_commit.content, setting),
                    'help_text': setting.description,
                }

                # Setting type customizations.
                if type(setting) == VACTemplaterLongTextSetting:
                    field_attrs['widget'] = forms.Textarea()

                elif type(setting) == VACTemplaterIntegerSetting:
                    field_attrs['required'] = True
                    if 'max' in setting.validators:
                        field_attrs['max_value'] = \
                            setting.validators['max']
                    if 'min' in setting.validators:
                        field_attrs['min_value'] = \
                            setting.validators['min']

                elif type(setting) == VACTemplaterSelectSetting:
                    field_attrs['required'] = True
                    field_attrs['choices'] = [
                        (option, option)
                        for option in setting.validators['options']]

                # Build field.
                self.fields[setting.id] = field_cls(**field_attrs)

    def _clean_setting(self, setting, cleaned_data):
        if type(setting) == VACTemplaterGroupSetting:
            for subsetting in setting.settings:
                self._clean_setting(subsetting, cleaned_data)
        elif setting.role in self.vac_templater_user.roles:
            value = cleaned_data.get(setting.id)
            if value is not None:
                try:
                    setting.validate(value)
                    field = self.fields[setting.id]
                    prefixed_name = self.add_prefix(setting.id)
                    data_value = field.widget.value_from_datadict(
                        self.data, self.files, prefixed_name)
                    if field.has_changed(field.initial, data_value):
                        self.changes.append(
                            (setting.name,
                             field.initial,
                             value))
                except ValidationError as e:
                    for error in e.messages:
                        self.add_error(
                            setting.id, forms.ValidationError(error))


class HistoryForm(forms.Form):
    ITEMS_PER_PAGE_CHOICES = [10, 20, 50]
    SORT_CRITERIA_CHOICES = (
        ('created_at', _('Creation date')),
    )

    user = FallbackCharField(
        widget=forms.TextInput(attrs={'placeholder': _('user')}),
        default='',
        max_length=128)

    group = FallbackCharField(
        widget=forms.TextInput(attrs={'placeholder': _('cache group')}),
        default='',
        max_length=128)

    branch = FallbackCharField(
        widget=forms.TextInput(attrs={'placeholder': _('VCL branch')}),
        default='',
        max_length=128)

    commit = FallbackCharField(
        widget=forms.TextInput(attrs={'placeholder': _('commit')}),
        default='',
        max_length=128)

    items_per_page = FallbackIntegerField(choices=ITEMS_PER_PAGE_CHOICES)

    page = FallbackIntegerField(default=1, min_value=1)

    sort_criteria = FallbackCharField(choices=[
        id for (id, name) in SORT_CRITERIA_CHOICES])

    sort_direction = SortDirectionField(default='desc')

    def __init__(self, *args, **kwargs):
        super(HistoryForm, self).__init__(*args, **kwargs)
        self.paginator = None

    def execute(self):
        self.paginator = Paginator(
            object_list=self._query_set(),
            per_page=self.cleaned_data.get('items_per_page'),
            page=self.cleaned_data.get('page'))

    def _query_set(self):
        order_by_prefix = \
            '-' if self.cleaned_data.get('sort_direction') == 'desc' else ''
        result = Deployment.objects.filter().\
            order_by(order_by_prefix + self.cleaned_data.get('sort_criteria'))
        if self.cleaned_data.get('user'):
            result = result.filter(
                user=self.cleaned_data.get('user'))
        if self.cleaned_data.get('group'):
            result = result.filter(
                Q(group_name__icontains=self.cleaned_data.get('group')) |
                Q(group_oid__startswith=self.cleaned_data.get('group')))
        if self.cleaned_data.get('branch'):
            result = result.filter(
                Q(branch_name__icontains=self.cleaned_data.get('branch')) |
                Q(branch_oid__startswith=self.cleaned_data.get('branch')))
        if self.cleaned_data.get('commit'):
            result = result.filter(
                Q(old_head_oid__startswith=self.cleaned_data.get('commit')) |
                Q(new_head_oid__startswith=self.cleaned_data.get('commit')))
        return result

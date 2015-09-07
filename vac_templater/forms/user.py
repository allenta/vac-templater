# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import authenticate


class LoginForm(forms.Form):
    username = forms.CharField(
        label=_('VAC username'),
        widget=forms.TextInput(attrs={'placeholder': _('VAC username')}),
        max_length=64)
    password = forms.CharField(
        label=_('VAC password'),
        widget=forms.PasswordInput(attrs={'placeholder': _('VAC password')}))
    destination = forms.CharField(
        widget=forms.HiddenInput())

    error_messages = {
        'invalid_login': _(
            'Please enter a correct VAC username and password. '
            'Note that both fields are case-sensitive.'),
        'inactive': _(
            'This account is inactive.'),
    }

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user = authenticate(username=username, password=password)
            if self.user is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'])
            elif not self.user.is_active:
                raise forms.ValidationError(
                    self.error_messages['inactive'])
        return self.cleaned_data

# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.conf import settings
from django.utils.encoding import smart_str
from django.utils import translation
from hashlib import sha1
from mediagenerator.generators.bundles.base import Filter
from mediagenerator.utils import find_file, read_text_file
from mediagenerator.filters import i18n

if settings.USE_I18N:
    LANGUAGES = [code for code, _ in settings.LANGUAGES]
else:
    LANGUAGES = (settings.LANGUAGE_CODE,)


class I18N(i18n.I18N):
    def _generate(self, language):
        # The mediagenerator I18N filter is not ready to be used with Django 1.8
        # (see https://docs.djangoproject.com/en/1.8/ref/utils/#django.utils.translation.get_language).
        # This is a temporary workaround while not fixed.
        with translation.override(language):
            return super(I18N, self)._generate(language)


class I18NFile(Filter):
    def __init__(self, **kwargs):
        self.config(kwargs, placeholder='##LANGUAGE##', file=None)
        super(I18NFile, self).__init__(**kwargs)

    def get_variations(self):
        return {'language': LANGUAGES}

    def get_output(self, variation):
        yield self._get_contents(variation['language'])

    def get_dev_output(self, name, variation):
        return self._get_contents(variation['language'])

    def get_dev_output_names(self, variation):
        filename = self._get_filename(variation['language'])
        hash = sha1(smart_str(self._get_contents(variation['language']))).hexdigest()
        yield filename, hash

    def _get_contents(self, language):
        filename = self._get_filename(language)
        path = find_file(filename)
        assert path, "File name '%s' doesn't exist." % filename
        return read_text_file(path)

    def _get_filename(self, language):
        return self.file.replace(self.placeholder, language)

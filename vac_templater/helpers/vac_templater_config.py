# -*- coding: utf-8 -*-

'''
:copyright: (c) 2015 by Allenta Consulting S.L. <info@allenta.com>.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import re
import yaml
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _


class VACTemplaterConfig(object):
    class ConfigError(Exception):
        def __init__(self, messages, *args, **kwargs):
            self.messages = messages
            super(VACTemplaterConfig.ConfigError, self).__init__(*args, **kwargs)

    def __init__(self, users=None, settings=None):
        self.users = users or []
        self.settings = settings or []

    @classmethod
    def parse(cls, vcl):
        '''Parse a VCL searching for a valid VAC Templater configuration.

        A VACTemplaterConfig.ConfigError exception is raised if any error is
        found in the configuration or in any usage of a setting in the VCL.
        Otherwise, a VACTemplaterConfig instance is be returned.

        '''
        # Default empty config.
        config = cls()

        # Iterate through comments searching for a VAC Templater config.
        for comment in re.finditer(r'\/\*.*?(vac-templater:.*?)\*\/',
                                   vcl,
                                   re.DOTALL | re.MULTILINE):
            try:
                parsed_config = yaml.load(
                    re.sub(r'\n \*', '\n', comment.group(1)))['vac-templater']
            except yaml.YAMLError as e:
                print e
            else:
                # Build instance from parsed config. This may raise a
                # VACTemplaterConfig.ConfigError exception if the config is
                # invalid.
                config = cls.build(parsed_config)

                # Extra check: validate usages of all settings in the VCL to
                # warn about invalid representations. This may raise a
                # VACTemplaterConfig.ConfigError exception.
                config.validate_usages(vcl)

                # Don't search anymore.
                break

        # Done!
        return config

    @classmethod
    def build(cls, parsed_config):
        '''Build a VACTemplaterConfig instance from a YAML parsed config.

        A VACTemplaterConfig.ConfigError exception is raised if any error is
        found in the configuration.

        '''
        config = None
        errors = []

        if isinstance(parsed_config, dict):
            users = []
            settings = []
            roles = set()

            # Parse users and build up a set of known roles.
            if 'users' in parsed_config:
                if isinstance(parsed_config['users'], list):
                    for user_config in parsed_config['users']:
                        try:
                            user = VACTemplaterUser.build(user_config)
                        except VACTemplaterConfig.ConfigError as e:
                            errors += e.messages
                        else:
                            users.append(user)
                            roles |= set(user.roles)
                else:
                    errors.append(
                        _('"users" entry must be a list'))

            # Parse settings.
            if 'settings' in parsed_config:
                if isinstance(parsed_config['settings'], list):
                    for setting_config in parsed_config['settings']:
                        try:
                            setting = VACTemplaterSetting.build(
                                roles, setting_config)
                        except VACTemplaterConfig.ConfigError as e:
                            errors += e.messages
                        else:
                            settings.append(setting)
                else:
                    errors.append(
                        _('"settings" entry must be a list'))

            config = cls(users, settings)
        else:
            errors.append(
                _('Invalid configuration: '
                  '%(parsed_config)s') % {
                    'parsed_config': parsed_config,
                })

        if errors:
            raise VACTemplaterConfig.ConfigError(errors)
        else:
            return config

    @classmethod
    def parse_value(cls, vcl, setting):
        '''Return the current value for a given setting in a certain VCL.

        The current value is extracted from the first usage of the setting.
        If no usage is done or if the current value is invalid, None is
        returned.

        '''
        match = re.search(
            r'/\* {{ %s(?:\|(\w+))? \*/(.*?)/\* }} \*/' % setting.id,
            vcl,
            re.DOTALL | re.MULTILINE)
        if match:
            representation = match.group(1)
            raw_value = match.group(2)
            try:
                return setting.to_python(raw_value, representation)
            except ValueError:
                pass
        return None

    def substitute(self, values, vcl):
        '''Substitute values for all current settings in a VCL.

        Only settings to which values have been provided are substituted.
        The new VCL is returned unless a ValueError exception is raised if any
        of the supplied values has an invalid type for the specific setting.

        '''
        return self._substitute(values, vcl, self.settings)

    def validate_usages(self, vcl, settings=None):
        '''Check that all variable usages are valid.

        If any invalid representation is being tried to be used for a certain
        setting, a VACTemplaterConfig.ConfigError exception is raised.

        '''
        return self._validate_usages(vcl, self.settings)

    def _substitute(self, values, vcl, settings):
        # Substitute all usages in the VCL of every setting for which values
        # were provided.
        for setting in settings:
            if type(setting) == VACTemplaterGroupSetting:
                vcl = self._substitute(values, vcl, setting.settings)
            elif setting.id in values:
                vcl = re.sub(
                    r'/\* {{ %s(\|(\w+))? \*/(.*?)/\* }} \*/' % setting.id,
                    lambda match, setting=setting: '/* {{ %(id)s%(representation)s */%(value)s/* }} */' % {
                        'id': setting.id,
                        'representation': match.group(1) or '',
                        'value': setting.to_vcl(
                            values[setting.id], match.group(2)),
                    },
                    vcl,
                    flags=re.DOTALL | re.MULTILINE)

        # Done!
        return vcl

    def _validate_usages(self, vcl, settings):
        errors = []

        # Check all usages for each setting.
        for setting in settings:
            if type(setting) == VACTemplaterGroupSetting:
                try:
                    self._validate_usages(vcl, setting.settings)
                except VACTemplaterConfig.ConfigError as e:
                    errors += e.messages
            else:
                for usage in re.finditer(
                        r'/\* {{ %s(?:\|(\w+))? \*/(.*?)/\* }} \*/' % setting.id,
                        vcl,
                        re.DOTALL | re.MULTILINE):
                    representation = usage.group(1)
                    if representation is not None and \
                       representation not in setting.REPRESENTATIONS:
                        errors.append(
                            'Invalid representation "%(representation)s" for '
                            'setting "%(setting)s"' % {
                                'representation': representation,
                                'setting': setting.id,
                            })

        # If any error was found, raise a ConfigError exception.
        if errors:
            raise VACTemplaterConfig.ConfigError(errors)


class VACTemplaterUser(object):
    def __init__(self, id, roles=None):
        self.id = id
        self.roles = roles if roles is not None else []

        # All users have the implicit "user" role.
        if 'user' not in self.roles:
            self.roles.append('user')

    @classmethod
    def build(cls, user_config):
        '''Build a VACTemplaterUser instance from a YAML parsed config.

        A VACTemplaterConfig.ConfigError exception is raised if any error is
        found in the configuration.

        '''
        user = None
        errors = []

        if isinstance(user_config, dict) and \
           len(user_config) == 1:
            id = user_config.keys()[0]
            roles = user_config.values()[0]
            if isinstance(roles, list) and \
               all(isinstance(role, basestring) for role in roles):
                user = VACTemplaterUser(id, roles)
            else:
                errors.append(
                    _('Invalid roles list for user "%(user)s": %(roles)s') % {
                        'user': id,
                        'roles': roles,
                    })
        else:
            errors.append(
                _('Invalid user configuration: '
                  '%(user_config)s') % {
                    'user_config': user_config,
                })

        if errors:
            raise VACTemplaterConfig.ConfigError(errors)
        else:
            return user


class VACTemplaterSetting(object):
    TYPE = None  # Type label to be used in the config. Subclasses should redefine this.
    REPRESENTATIONS = ()  # Valid representations for this type. Subclasses should redefine this.

    def __init__(self, id, name=None, description=None, role=None, validators=None):
        self.id = id
        self.name = name if name is not None else id
        self.description = description
        self.role = role if role is not None else 'user'
        self.validators = validators if validators else {}

    @classmethod
    def build(cls, roles, setting_config, prefix='', default_role=None):
        '''Build a VACTemplaterSetting instance from a YAML parsed config.

        A VACTemplaterConfig.ConfigError exception is raised if any error is
        found.

        '''
        setting = None
        errors = []

        if isinstance(setting_config, dict) and \
           len(setting_config) == 1 and \
           isinstance(setting_config.values()[0], dict):
            id = prefix + setting_config.keys()[0]
            type = None

            # Parse type (optional. Defaults to VACTemplaterTextSetting).
            if 'type' in setting_config.values()[0]:
                type_id = setting_config.values()[0]['type']
                try:
                    type = next(
                        (subclass for subclass in VACTemplaterSetting.subclasses()
                         if subclass.TYPE == type_id))
                except StopIteration:
                    errors.append(
                        _('Invalid type for setting "%(setting)s": '
                          '%(type)s') % {
                            'type': type_id,
                            'setting': id,
                        })
            else:
                type = VACTemplaterTextSetting

            if type:
                try:
                    # Extract instantiation args.
                    args = type.extract_args(
                        id, roles, setting_config.values()[0])

                    # Add the provided default role, if any.
                    if default_role:
                        args.setdefault('role', default_role)

                    # Build the setting.
                    setting = type(id, **args)
                except VACTemplaterConfig.ConfigError as e:
                    errors += e.messages
        else:
            errors.append(
                _('Invalid setting: %(setting)s') % {
                    'setting': setting_config,
                })

        if errors:
            raise VACTemplaterConfig.ConfigError(errors)
        else:
            return setting

    @classmethod
    def extract_args(cls, id, roles, setting_config):
        '''Collect arguments from the parsed config for setting instantiation.

        A VACTemplaterConfig.ConfigError exception is raised if any error is
        found. Subclasses may redefine this to add extra checks or to collect
        extra arguments specific to their type.

        '''
        args = {}
        errors = []

        # Parse name (optional. Defaults to id).
        if 'name' in setting_config:
            name = setting_config['name']
            if isinstance(name, basestring):
                args['name'] = name
            else:
                errors.append(
                    _('Invalid name for setting "%(setting)s": %(name)s') % {
                        'setting': id,
                        'name': name,
                    })

        # Parse description (optional).
        if 'description' in setting_config:
            description = setting_config['description']
            if isinstance(description, basestring):
                args['description'] = description
            else:
                errors.append(
                    _('Invalid description for setting "%(setting)s": '
                      '%(description)s') % {
                        'setting': id,
                        'description': description,
                    })

        # Parse role (optional. Defaults to 'user').
        if 'role' in setting_config:
            role = setting_config['role']
            if isinstance(role, basestring) and \
               role in roles:
                args['role'] = role
            else:
                errors.append(
                    _('Unknown role for setting "%(setting)s": %(role)s') % {
                        'setting': id,
                        'role': role,
                    })

        # Parse validators (optional. Defaults to empty dict).
        if 'validators' in setting_config:
            validators = setting_config['validators']
            if isinstance(validators, dict):
                args['validators'] = {}

                # Check validators.
                for validator, value in validators.iteritems():
                    try:
                        args['validators'][validator] = \
                            cls._build_validator(id, validator, value)
                    except VACTemplaterConfig.ConfigError as e:
                        errors += e.messages
            else:
                errors.append(
                    _('Invalid validators for setting "%(setting)s": '
                      '%(validators)s') % {
                        'setting': id,
                        'validators': validators,
                    })

        if errors:
            raise VACTemplaterConfig.ConfigError(errors)
        else:
            return args

    @classmethod
    def subclasses(cls):
        subclasses = []
        for child in cls.__subclasses__():
            subclasses.append(child)
            subclasses += child.subclasses()
        return subclasses

    @classmethod
    def to_vcl(cls, value, representation=None):
        '''Convert a Python object to a raw value valid to be used in a VCL.

        A ValueError exception is raised if no conversion can be done.
        By default, no representation is valid. Subclasses should redefine this
        method to support different representations per type.

        '''
        # Convert!
        if not representation:
            return str(value)

        # No conversion done? Fail.
        raise ValueError()

    @classmethod
    def to_python(cls, raw_value, representation=None):
        '''Convert a raw value extracted from a VCL to a python object.

        A ValueError exception is raised if no conversion can be done.
        By default, no representation is valid. Subclasses should redefine this
        method to support different representations per type.

        '''
        # Convert!
        if not representation:
            return raw_value

        # No conversion done? Fail.
        raise ValueError()

    @classmethod
    def _build_validator(cls, id, validator, value):
        '''Parses a validator specification.

        The processed value to be used as the specification of the validator is
        returned if both the value and the validator are valid.
        A VACTemplaterConfig.ConfigError exception is raised if any error is
        found. Subclasses should redefine this method to support their own validators.

        '''
        # By default, no validator is expected.
        raise VACTemplaterConfig.ConfigError([
            _('Invalid validator for setting "%(setting)s": '
              '%(validator)s.') % {
                'setting': id,
                'validator': validator,
            }])

    def validate(self, value):
        '''Check if value is valid by running it through all validators.

        A ValidationError exception is raised with all error messages, if any.
        Subclasses should redefine this method to support their own validators.

        '''
        # No validations to be done by default.
        pass


class VACTemplaterTextSetting(VACTemplaterSetting):
    TYPE = 'text'

    @classmethod
    def to_vcl(cls, value, representation=None):
        # Default representation is "str".
        representation = representation or 'str'

        # Convert!
        if isinstance(value, basestring):
            if representation == 'str':
                return '"%s"' % value

        # No conversion done? Fail.
        raise ValueError()

    @classmethod
    def to_python(cls, raw_value, representation=None):
        # Default representation is "str".
        representation = representation or 'str'

        # Convert!
        if representation == 'str' and \
           raw_value[0] == raw_value[-1] == '"':
            return raw_value[1:-1]

        # No conversion done? Fail.
        raise ValueError()

    @classmethod
    def _build_validator(cls, id, validator, value):
        if validator in ('min', 'max'):
            if isinstance(value, int):
                return value
            else:
                raise VACTemplaterConfig.ConfigError([
                    _('"%(validator)s" validator for setting "%(setting)s" '
                      'should be an integer.') % {
                        'validator': validator,
                        'setting': id,
                    }])
        elif validator == 'regexp':
            if isinstance(value, basestring):
                return value
            else:
                raise VACTemplaterConfig.ConfigError([
                    _('"regexp" validator for setting "%(setting)s" should be '
                      'a string.') % {
                        'setting': id,
                    }])
        else:
            return super(VACTemplaterTextSetting, cls)._build_validator(
                id, validator, value)

    def validate(self, value):
        errors = []

        try:
            super(VACTemplaterTextSetting, self).validate(value)
        except ValidationError as e:
            errors += e.messages

        if 'min' in self.validators and \
           len(value) < self.validators['min']:
            errors.append(_('Value is too short. Min chars are %(min)d.') % {
                'min': self.validators['min'],
            })

        if 'max' in self.validators and \
           len(value) > self.validators['max']:
            errors.append(_('Value is too long. Max chars are %(max)d.') % {
                'max': self.validators['max'],
            })

        if 'regexp' in self.validators and \
           not re.match(self.validators['regexp'], value):
            errors.append(_('Invalid format.'))

        if errors:
            raise ValidationError(errors)


class VACTemplaterLongTextSetting(VACTemplaterTextSetting):
    TYPE = 'longtext'

    @classmethod
    def to_vcl(cls, value, representation=None):
        # Default representation is "str".
        representation = representation or 'str'

        # Convert!
        if isinstance(value, basestring):
            if representation == 'str':
                return '{"%s"}' % value

        # No conversion done? Fail.
        raise ValueError()

    @classmethod
    def to_python(cls, raw_value, representation=None):
        # Default representation is "str".
        representation = representation or 'str'

        # Convert!
        if representation == 'str' and \
           raw_value.startswith('{"') and \
           raw_value.endswith('"}'):
            return raw_value[2:-2]

        # No conversion done? Fail.
        raise ValueError()


class VACTemplaterIntegerSetting(VACTemplaterSetting):
    TYPE = 'integer'
    REPRESENTATIONS = ('int', 'str')

    @classmethod
    def to_vcl(cls, value, representation=None):
        # Default representation is "int".
        representation = representation or 'int'

        # Convert!
        if isinstance(value, int):
            if representation == 'int':
                return '%d' % value
            elif representation == 'str':
                return '"%d"' % value

        # No conversion done? Fail.
        raise ValueError()

    @classmethod
    def to_python(cls, raw_value, representation=None):
        # Default representation is "int".
        representation = representation or 'int'

        # Convert!
        if representation == 'int' and \
           raw_value.isdigit():
            return int(raw_value)
        elif representation == 'str' and \
                raw_value[0] == raw_value[-1] == '"':
            return int(raw_value[1:-1])

        # No conversion done? Fail.
        raise ValueError()

    @classmethod
    def _build_validator(cls, id, validator, value):
        if validator in ('min', 'max'):
            if isinstance(value, int):
                return value
            else:
                raise VACTemplaterConfig.ConfigError([
                    _('"%(validator)s" validator for setting "%(setting)s" '
                      'should be an integer.') % {
                        'validator': validator,
                        'setting': id,
                    }])
        else:
            return super(VACTemplaterIntegerSetting, cls)._build_validator(
                id, validator, value)

    def validate(self, value):
        errors = []

        try:
            super(VACTemplaterIntegerSetting, self).validate(value)
        except ValidationError as e:
            errors += e.messages

        if 'min' in self.validators and \
           value < self.validators['min']:
            errors.append(_('Value is too small. Minimum is %(min)d.') % {
                'min': self.validators['min'],
            })

        if 'max' in self.validators and \
           value > self.validators['max']:
            errors.append(_('Value is too big. Maximum as %(max)d.') % {
                'max': self.validators['max'],
            })

        if errors:
            raise ValidationError(errors)


class VACTemplaterDurationSetting(VACTemplaterSetting):
    TYPE = 'duration'
    DURATIONS = {
        'ms': {
            'label': _('milliseconds'),
            'ms': 1,
        },
        's': {
            'label': _('seconds'),
            'ms': 1000,
        },
        'm': {
            'label': _('minutes'),
            'ms': 60 * 1000,
        },
        'h': {
            'label': _('hours'),
            'ms': 60 * 60 * 1000,
        },
        'd': {
            'label': _('days'),
            'ms': 24 * 60 * 60 * 1000,
        },
        'w': {
            'label': _('weeks'),
            'ms': 7 * 24 * 60 * 60 * 1000,
        },
    }

    @classmethod
    def to_vcl(cls, value, representation=None):
        # Default representation is "duration".
        representation = representation or 'duration'

        # Convert!
        if isinstance(value, tuple) and \
           len(value) == 2 and \
           isinstance(value[0], float) and \
           isinstance(value[1], basestring):
            if representation == 'duration':
                return "%s%s" % (
                    str(value[0] if (value[0] % 1 > 0) else int(value[0])),
                    value[1],
                )

        # No conversion done? Fail.
        raise ValueError()

    @classmethod
    def to_python(cls, raw_value, representation=None):
        # Default representation is "duration".
        representation = representation or 'duration'

        # Convert!
        if representation == 'duration':
            match = re.match(
                r'^([0-9]*\.?[0-9]+)(%s)$' % '|'.join(cls.DURATIONS.keys()), raw_value)
            if match is not None:
                return (float(match.group(1)), match.group(2))

        # No conversion done? Fail.
        raise ValueError()

    @classmethod
    def _build_validator(cls, id, validator, value):
        if validator in ('min', 'max'):
            if isinstance(value, basestring):
                try:
                    return cls.to_python(value)
                except ValueError:
                    raise VACTemplaterConfig.ConfigError([
                        _('Invalid duration at "%(validator)s" validator for '
                          'setting "%(setting)s": %(duration)s') % {
                            'validator': validator,
                            'setting': id,
                            'duration': value,
                        }])
            else:
                raise VACTemplaterConfig.ConfigError([
                    _('"%(validator)s" validator for setting "%(setting)s" '
                      'should be a valid string.') % {
                        'validator': validator,
                        'setting': id,
                    }])
        else:
            return super(VACTemplaterDurationSetting, cls)._build_validator(
                id, validator, value)

    def validate(self, value):
        errors = []

        try:
            super(VACTemplaterDurationSetting, self).validate(value)
        except ValidationError as e:
            errors += e.messages

        if value[0] < 0:
            errors.append(_('Duration must be positive.'))

        value_in_milliseconds = value[0] * self.DURATIONS[value[1]]['ms']

        if 'min' in self.validators and \
           value_in_milliseconds < self.validators['min'][0] * self.DURATIONS[self.validators['min'][1]]['ms']:
            errors.append(_('Value is too small. Minimum is %(min)s.') % {
                'min': self.to_vcl(self.validators['min']),
            })

        if 'max' in self.validators and \
           value_in_milliseconds > self.validators['max'][0] * self.DURATIONS[self.validators['max'][1]]['ms']:
            errors.append(_('Value is too big. Maximum is %(max)s.') % {
                'max': self.to_vcl(self.validators['max']),
            })

        if errors:
            raise ValidationError(errors)


class VACTemplaterBooleanSetting(VACTemplaterSetting):
    TYPE = 'boolean'
    REPRESENTATIONS = ('bool', 'int', 'str')

    @classmethod
    def to_vcl(cls, value, representation=None):
        # Default representation is "bool".
        representation = representation or 'bool'

        # Convert!
        if isinstance(value, bool):
            if representation == 'bool':
                return 'true' if value else 'false'
            elif representation == 'int':
                return '1' if value else '0'
            elif representation == 'str':
                return '"1"' if value else '"0"'

        # No conversion done? Fail.
        raise ValueError()

    @classmethod
    def to_python(cls, raw_value, representation=None):
        # Default representation is "bool".
        representation = representation or 'bool'

        # Convert!
        if representation == 'bool' and \
           raw_value in ('true', 'false'):
            return raw_value == 'true'
        elif representation == 'int' and \
                raw_value.isdigit():
            return raw_value == '1'
        elif representation == 'str' and \
                raw_value[0] == raw_value[-1] == '"':
            return raw_value == '"1"'

        # No conversion done? Fail.
        raise ValueError()


class VACTemplaterACLSetting(VACTemplaterSetting):
    TYPE = 'acl'

    @classmethod
    def to_vcl(cls, value, representation=None):
        # Convert!
        if isinstance(value, list) and \
           all(isinstance(val, basestring) for val in value):
            if representation is None:
                return '\n' + '\n'.join('%s;' % val for val in value) + '\n'

        # No conversion done? Fail.
        raise ValueError()

    @classmethod
    def to_python(cls, raw_value, representation=None):
        # Convert!
        if representation is None:
            return [value.strip() for value in raw_value.split(';')[:-1]]

        # No conversion done? Fail.
        raise ValueError()

    def validate(self, value):
        errors = []

        try:
            super(VACTemplaterACLSetting, self).validate(value)
        except ValidationError as e:
            errors += e.messages

        for val in value:
            if not re.match(r'^\s*\!?\s*"[^"]+"(\/\d+)?\s*$', val) and \
               not re.match(r'^\s*\(\!?\s*"[^"]+"(\/\d+)?\)\s*$', val):
                errors.append(_('Invalid value: %(val)s.') % {
                    'val': val,
                })

        if errors:
            raise ValidationError(errors)


class VACTemplaterSelectSetting(VACTemplaterSetting):
    TYPE = 'select'

    @classmethod
    def extract_args(cls, id, roles, setting_config):
        args = {}
        errors = []

        try:
            args.update(super(VACTemplaterSelectSetting, cls).extract_args(
                id, roles, setting_config))
        except VACTemplaterConfig.ConfigError as e:
            errors += e.messages

        # Extra validators check: 'options' validator is mandatory.
        if 'validators' not in setting_config or \
           (isinstance(setting_config['validators'], dict) and
                'options' not in setting_config['validators']):
            errors.append(
                _('Setting "%(setting)s" must provide an "options" '
                  'validator.') % {
                    'setting': id,
                })

        if errors:
            raise VACTemplaterConfig.ConfigError(messages=errors)
        else:
            return args

    @classmethod
    def to_vcl(cls, value, representation=None):
        # Default representation is "str".
        representation = representation or 'str'

        # Convert!
        if isinstance(value, basestring):
            if representation == 'str':
                return '"%s"' % value

        # No conversion done? Fail.
        raise ValueError()

    @classmethod
    def to_python(cls, raw_value, representation=None):
        # Default representation is "str".
        representation = representation or 'str'

        # Convert!
        if representation == 'str' and \
           raw_value[0] == raw_value[-1] == '"':
            return raw_value[1:-1]

        # No conversion done? Fail.
        raise ValueError()

    @classmethod
    def _build_validator(cls, id, validator, value):
        if validator == 'options':
            if isinstance(value, list):
                errors = []
                for option in value:
                    if not isinstance(option, basestring):
                        errors.append(
                            _('Invalid option for setting "%(setting)s": '
                              '%(option)s') % {
                                'setting': id,
                                'option': option,
                            })
                if errors:
                    raise VACTemplaterConfig.ConfigError(errors)
                else:
                    return value
            else:
                raise VACTemplaterConfig.ConfigError([
                    _('"options" validator for setting "%(setting)s" '
                      'should be a list.') % {
                        'setting': id,
                    }])
        else:
            return super(VACTemplaterSelectSetting, cls)._build_validator(
                id, validator, value)

    def validate(self, value):
        errors = []

        try:
            super(VACTemplaterSelectSetting, self).validate(value)
        except ValidationError as e:
            errors += e.messages

        if value not in self.validators['options']:
            errors.append(_('Invalid choice.'))

        if errors:
            raise ValidationError(errors)


class VACTemplaterGroupSetting(VACTemplaterSetting):
    TYPE = 'group'

    def __init__(self, id, settings=None, **kwargs):
        super(VACTemplaterGroupSetting, self).__init__(id, **kwargs)
        self.settings = settings if settings is not None else []

    @classmethod
    def extract_args(cls, id, roles, setting_config):
        args = {}
        errors = []

        try:
            args.update(super(VACTemplaterGroupSetting, cls).extract_args(
                id, roles, setting_config))
        except VACTemplaterConfig.ConfigError as e:
            errors += e.messages

        # Parse extra settings argument (optional).
        args['settings'] = []
        if 'settings' in setting_config:
            subsettings_config = setting_config['settings']
            if isinstance(subsettings_config, list):
                for subsetting_config in subsettings_config:
                    try:
                        subsetting = VACTemplaterSetting.build(
                            roles,
                            subsetting_config,
                            prefix=id + ':',
                            default_role=args.get('role'))
                        args['settings'].append(subsetting)
                    except VACTemplaterConfig.ConfigError as e:
                        errors += e.messages
            else:
                errors.append(
                    _('Invalid settings for group "%(setting)s"') % {
                        'setting': id,
                    })

        if errors:
            raise VACTemplaterConfig.ConfigError(messages=errors)
        else:
            return args

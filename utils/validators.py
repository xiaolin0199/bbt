# coding=utf-8
from __future__ import unicode_literals

import re
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.core.validators import _lazy_re_compile as lazy_re_compile, RegexValidator


@deconstructible
class RangeValidator(RegexValidator):
    message = _('Enter a valid port range.')

    def __init__(self, sep=',', message=None, code='invalid', allow_negative=False, greed_mode=True, **kwargs):
        super(RangeValidator, self).__init__(**kwargs)
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code

        self.regexp = lazy_re_compile('^%(neg)s\d+(?:%(sep)s%(neg)s\d+)%(greed)s\Z' % {
            'neg': '(-)?' if allow_negative else '',
            'sep': re.escape(sep),
            'greed': greed_mode and '*' or '?'
        })

    def __call__(self, value):
        value = force_text(value)

        try:
            super(RangeValidator, self).__call__(value)
        except ValidationError as e:
            raise e


@deconstructible
class PortRangeValidator(RangeValidator):
    message = _('Range start should be less then range end.')
    bad_range = _('Range number should be in the range from 1 to 65535.')
    port_range_min = 1
    port_range_max = 65535

    def __call__(self, value):
        value = force_text(value)

        try:
            super(PortRangeValidator, self).__call__(value)
        except ValidationError as e:
            raise e

        else:
            range_begin, range_end = value.rsplit(':', 1)
            if not (self.port_range_min <= int(range_begin) <= self.port_range_max):
                raise ValidationError(self.bad_range, code=self.code)
            elif not (self.port_range_min <= int(range_end) <= self.port_range_max):
                raise ValidationError(self.bad_range, code=self.code)
            elif int(range_begin) > int(range_end):
                raise ValidationError(self.message, code=self.code)


validate_colon_separated_port_range = PortRangeValidator(sep=':')

# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import time
import dateutil.parser

from dinase.sugar.future import string_types
from dinase.sugar.future import default_integer_type as int

from .const import SECONDS_IN_HOUR
from .convert import to_timestamp
from .standard import xsd, rfc2822, rfc822


def parse(string):
    for obj in (xsd, rfc2822, rfc822, dateutil.parser):
        try:
            return obj.parse(string)
        except ValueError:
            pass

    raise ValueError("can not parse: {}".format(string))


def get_age(value):
    if isinstance(value, string_types):
        value = parse(value)

    value = to_timestamp(value)

    return int((time.time() - value) / SECONDS_IN_HOUR)

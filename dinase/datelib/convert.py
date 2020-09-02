# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import time
from datetime import datetime
import calendar

from dateutil.tz import tzutc, tzlocal

from dinase.sugar.future import integer_types


def timestamp_to_struct_time(timestamp, utc=False):
    if utc:
        return time.gmtime(timestamp)
    else:
        return time.localtime(timestamp)


def struct_time_to_timestamp(struct_time, utc=False):
    if utc:
        return calendar.timegm(struct_time)
    else:
        return time.mktime(struct_time)


def datetime_to_struct_time(dt, utc=False):
    if utc:
        return dt.utctimetuple()
    else:
        return dt.timetuple()


def struct_time_to_datetime(struct_time, utc=None):
    return timestamp_to_datetime(
        struct_time_to_timestamp(struct_time, utc),
        utc
    )


def datetime_to_timestamp(dt):
    return struct_time_to_timestamp(
        datetime_to_struct_time(dt, utc=True),
        utc=True
    )


def timestamp_to_datetime(timestamp, utc=None):
    if utc is None:
        return datetime.fromtimestamp(timestamp)
    elif utc:
        return datetime.fromtimestamp(timestamp, tzutc())
    else:
        return datetime.fromtimestamp(timestamp, tzlocal())


_convmap = (
    (datetime,                 time.struct_time,  datetime_to_struct_time),
    (datetime,                 float,             datetime_to_timestamp),
    (time.struct_time,         datetime,          struct_time_to_datetime),
    (time.struct_time,         float,             struct_time_to_timestamp),
    (integer_types + (float,), datetime,          timestamp_to_datetime),
    (integer_types + (float,), time.struct_time,  timestamp_to_struct_time),
)


def _converter(value, class_to, *args, **kwargs):
    if isinstance(value, class_to):
        return value

    for conv_class_from, conv_class_to, conv_func in _convmap:
        if not isinstance(value, conv_class_from):
            continue

        if not issubclass(class_to, conv_class_to):
            continue

        return conv_func(value, *args, **kwargs)

    raise ValueError("unknow datetime type: {}".format(
        value.__class__.__name__))


def to_struct_time(value, *args, **kwargs):
    return _converter(value, time.struct_time, *args, **kwargs)


def to_timestamp(value, *args, **kwargs):
    return _converter(value, float, *args, **kwargs)


def to_datetime(value, *args, **kwargs):
    return _converter(value, datetime, *args, **kwargs)

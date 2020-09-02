# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re
import datetime
import dateutil.tz

from dinase.sugar.future import default_integer_type as int

from .const import SECONDS_IN_MINUTE, SECONDS_IN_HOUR, SECONDS_IN_DAY


# http://tools.ietf.org/html/rfc2822.html#section-3.3
# http://tools.ietf.org/html/rfc822.html#section-5
# http://tools.ietf.org/html/rfc3339.html#section-5.6
# http://www.w3.org/TR/NOTE-datetime


class _DateTimeBase(object):

    regex = None

    @classmethod
    def validate(cls, string):
        return cls.regex.match(string) is not None

    @staticmethod
    def _parse_offset(offset):
        parsed = re.match(r"^(?P<sign>[+-])(?P<hours>[\d]{2}):?(?P<minutes>[\d]{2})$", offset)

        return (-1 if parsed.group("sign") == "-" else 1) * \
               (int(parsed.group("hours")) * 3600 + int(parsed.group("minutes")) * 60)


class rfc2822(_DateTimeBase):

    regex = re.compile(r"^(?P<datetime>[A-Z][a-z]{2}, "
                       r"\d{2} [A-Z][a-z]{2} \d{4} \d{2}:\d{2}:\d{2}) "
                       r"(?P<offset>[+-]\d{4})$")

    @classmethod
    def parse(cls, string):
        parsed = cls.regex.match(string)

        if parsed is None:
            raise ValueError("string does not match rfc2822 format: {}"
                             .format(string))

        dt = datetime.datetime.strptime(parsed.group("datetime"),
                                        "%a, %d %b %Y %H:%M:%S")
        tz = dateutil.tz.tzoffset("UTC", cls._parse_offset(parsed.group("offset")))

        return dt.replace(tzinfo=tz)

    @staticmethod
    def format(dt, localtime=True):
        if localtime and dt.utcoffset() is None:
            dt = dt.replace(tzinfo=dateutil.tz.tzlocal())

        offset_mask = " %z" if dt.utcoffset() else " +0000"

        return dt.strftime("%a, %d %b %Y %H:%M:%S" + offset_mask)


class rfc822(_DateTimeBase):

    regex = re.compile(r"^(?P<datetime>[A-Z][a-z]{2}, "
                       r"\d{2} [A-Z][a-z]{2} \d{4} \d{2}:\d{2}:\d{2}) "
                       r"(?P<timezone>[A-Z]{3})(?: (?P<offset>[+-][\d]{4}))?$")

    @classmethod
    def parse(cls, string):
        parsed = cls.regex.match(string)

        if parsed is None:
            raise ValueError("string does not match rfc822 format: {}"
                             .format(string))

        dt = datetime.datetime.strptime(parsed.group("datetime"),
                                        "%a, %d %b %Y %H:%M:%S")
        offset = parsed.group("offset")
        offset = cls._parse_offset(offset) if offset else 0
        tz = dateutil.tz.tzoffset("UTC", offset)

        return dt.replace(tzinfo=tz)

    @staticmethod
    def format(dt, localtime=True):
        if localtime and dt.utcoffset() is None:
            dt = dt.replace(tzinfo=dateutil.tz.tzlocal())

        if dt.utcoffset() is None or dt.utcoffset() == datetime.timedelta(0):
            offset_mask = ""

        else:
            offset_mask = " %z"

        return dt.strftime("%a, %d %b %Y %H:%M:%S GMT" + offset_mask)


class xsd(_DateTimeBase):

    regex = re.compile(r"^(?P<era_sign>-)?(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
                       r"(?:\.(?P<milliseconds>\d+))?(?P<offset>Z|[+-]\d{2}:\d{2})$")

    @classmethod
    def parse(cls, string):
        parsed = cls.regex.match(string)

        if parsed is None:
            raise ValueError("string does not match xsd:dateTime format: {}".format(string))

        dt = datetime.datetime.strptime(parsed.group("datetime"), "%Y-%m-%dT%H:%M:%S")

        if parsed.group("milliseconds") is not None:
            dt = dt.replace(milliseconds=int(parsed.group("milliseconds")))

        if parsed.group("offset") is None:
            return dt

        if parsed.group("offset") == "Z":
            return dt.replace(tzinfo=dateutil.tz.tzutc())

        tz_offset = cls._parse_offset(parsed.group("offset"))
        tz = dateutil.tz.tzoffset("UTC", tz_offset)

        return dt.replace(tzinfo=tz)

    @staticmethod
    def format(dt, localtime=True):
        if localtime and dt.utcoffset() is None:
            dt = dt.replace(tzinfo=dateutil.tz.tzlocal())

        if dt.utcoffset() is None or dt.utcoffset() == datetime.timedelta(0):
            offset_mask = "Z"

        else:
            offset = dt.utcoffset()
            offset_in_seconds = abs(offset.seconds + offset.days * SECONDS_IN_DAY)
            sign = "+" if offset.days >= 0 else "-"
            offset_mask = "{}{:02d}:{:02d}".format(
                sign, offset_in_seconds / SECONDS_IN_HOUR,
                (offset_in_seconds % SECONDS_IN_HOUR) / SECONDS_IN_MINUTE)

        return dt.strftime("%Y-%m-%dT%H:%M:%S" + offset_mask)

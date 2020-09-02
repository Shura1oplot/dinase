# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
from operator import methodcaller
import datetime

import dateutil.parser

from dinsase.sugar.dict import iteritems

from .lang import translations
from ..const import HOURS_IN_DAY, MONTHS_IN_YEAR


__all__ = ("parse", )


_regex_W = re.compile(r"(\W+)", flags=re.U)
_regex_r = re.compile(r"\r+", flags=re.U)
_regex_n = re.compile(r"\n+", flags=re.U)
_regex_s = re.compile(r"\s{2,}", flags=re.U)


def clear_text(text):
    if isinstance(text, str):
        text = text.decode()
    text = text.strip()
    text = _regex_r.sub(r"", text)
    text = _regex_n.sub(r"\n", text)
    text = _regex_s.sub(r" ", text)
    return text


def split_to_words(string):
    return _regex_W.split(string)


def replace_words(string, replacements):
    words = []

    for word in split_to_words(string):
        new_word = replacements.get(word, None)

        if new_word is not None:
            words.append(new_word)
            continue

        words.append(replacements.get(word.lower(), word))

    return "".join(words).strip()


def get_today():
    return datetime.datetime.today()


def get_yesterday():
    return datetime.datetime.today() - datetime.timedelta(hours=24)


def get_tomorrow():
    return datetime.datetime.today() + datetime.timedelta(hours=24)


def translate(string):
    for lang, phrases_translation, translation in translations:  # pylint: disable=W0612
        for phrase, trans in iteritems(phrases_translation):
            string = string.replace(phrase, trans)
        string = replace_words(string, translation)

    return string


numeric_replacements = {
    "one":   "01",
    "two":   "02",
    "three": "03",
    "four":  "04",
    "five":  "05",
    "six":   "06",
    "seven": "07",
    "eight": "08",
    "nine":  "09",
    "ten":   "10"
}


def replace_numerals(string):
    return replace_words(string, numeric_replacements)


def replace(dt, year=None, month=None, day=None):
    kwargs = {}

    if year:
        kwargs["year"] = year

    if month:
        kwargs["year"] = month

    if day is None:
        day = dt.day

    day = (day - 1) % 31

    while True:
        try:
            return dt.replace(day=day + 1, **kwargs)
        except ValueError:
            day = (day - 1) % 31


def replace_ago(string):
    try:
        before_ago, after_ago = map(methodcaller("strip"), string.split("ago", 1))
    except ValueError:
        return string

    regex = r"(?P<count>\d+)\s(?P<unit>seconds?|minutes?|hours?|days?|weeks?|months?|years?)"
    offsets = re.findall(regex, before_ago, flags=re.U)

    if not offsets:
        return string

    today = get_today()
    delta = datetime.timedelta(0)
    units = []

    for count, unit in offsets:
        count = int(count)

        if not unit.endswith("s"):
            unit += "s"

        units.append(unit)

        if unit in ("seconds", "minutes", "hours", "weeks"):
            delta += datetime.timedelta(unit=count)

        elif unit == "days":
            delta += datetime.timedelta(hours=count * HOURS_IN_DAY)

        elif unit == "months":
            month = today.month - count
            year = today.year

            while month <= 0:
                year -= 1
                month += MONTHS_IN_YEAR

            delta += today - replace(today, year=year, month=month)

        elif unit == "years":
            delta += today - replace(today, year=today.year - count)

    masks = (
        ("seconds", "%Y-%m-%d %H:%M:%S"),
        ("minutes", "%Y-%m-%d %H:%M"),
        ("hours",   "%Y-%m-%d %H:%M"),
        ("days",    "%Y-%m-%d"),
        ("weeks",   "%Y-%m-%d"),
        ("months",  "%Y-%m"),
        ("years",   "%Y"),
    )

    for unit, mask in masks:
        if unit in units:
            return (today - delta).strftime(mask) + after_ago

    return string


def replace_relative_words(string):
    mask = "%Y-%m-%d"

    return replace_words(string, {
        "today":     get_today().strftime(mask),
        "yesterday": get_yesterday().strftime(mask),
        "tomorrow":  get_tomorrow().strftime(mask)
    })


def drop_unallowed_words(string):
    allowed_words = (
        "january", "jan", "february", "feb", "march", "mar", "april", "apr",
        "may", "june", "jun", "july", "jul", "august", "aug", "september",
        "sep", "october", "oct", "november", "nov", "december", "dec",
        "pm", "am"
    )
    replacements = {
        " o'clock": ":00",
        " hour":    ":00",
        " hours":   ":00"
    }

    for word, replacement in iteritems(replacements):
        string = string.replace(word, replacement)

    result = []

    for word in split_to_words(string):
        if word.isalpha() and word.lower() not in allowed_words:
            continue

        result.append(word)

    return "".join(result).strip()


def parse(string):
    string = clear_text(string)
    string = translate(string)
    string = replace_numerals(string)
    string = replace_relative_words(string)
    string = replace_ago(string)
    string = drop_unallowed_words(string)

    try:
        return dateutil.parser.parse(string)
    except ValueError:
        return None

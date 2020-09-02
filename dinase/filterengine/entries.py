# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from dinase.logiclib import filters

from .. import datelib
from ..config import feeds


class EntryRuleDateTime(filters.RuleDateTimeBase):

    _keys = ("updated", "published")

    def _parse(self, value):
        return datelib.parse(value)


def _get_age(value):
    return int(datelib.get_age(value) / datelib.HOURS_IN_DAY)


class EntryFilter(filters.Filter):

    _rules = (
        filters.RuleNumeric,
        filters.RuleListAsValue,
        filters.RuleListAsOperand,
        filters.RuleString,
        filters.RuleRegex,
        filters.RulePattern,
        EntryRuleDateTime,
    )

    _default_arguments = {
        "ignore_case": True
    }

    _aliases = {
        "feed": "_feed",
        "added": "_added",
        "title": "title.value",
        "summary": "summary.value",
    }

    _virtuals = {
        "usertags": lambda item: feeds[item["_feed"]].get("usertags", []),
        "age": lambda item: _get_age(item["updated"]),
        "added_ago": lambda item: _get_age(item["_added"]),
    }

    _defaults = {
        "title": {"value": ""},
        "summary": {"value": ""},
    }

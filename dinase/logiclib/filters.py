# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import operator
import re
import datetime
import trafaret as t

from dinase.sugar.future import string_types, integer_types
from dinase.sugar.coll import isempty
from dinase.sugar.func import complement
from dinase.sugar.dict import iteritems


class RelevanceLevel(object):

    inapplicable    = 0b00000000
    exception_guard = 0b00000001
    type_matching   = 0b00000011
    value_matching  = 0b00000101
    key_matching    = 0b00001001


class RuleError(Exception):
    pass


class RuleBase(object):

    _keys = None

    _operators = {}
    _aliases   = {}

    _operand_types = (object, )
    _value_types   = (object, )

    def __init__(self, rule, getter):
        super(RuleBase, self).__init__()

        key = rule["key"]

        if self._keys and key not in self._keys:
            raise RuleError("unallowed key: {}".format(key))

        opcode = rule["operator"]
        invert = rule.get("invert", False)

        while True:
            if opcode in self._aliases:
                opcode = self._aliases[opcode]
                continue
            if opcode.startswith("not_"):
                invert = not invert
                opcode = opcode[4:]
                continue
            break

        try:
            operator_ = self._operators[opcode]
        except KeyError:
            raise RuleError("unallowed opcode: {}".format(opcode))

        if invert:
            operator_ = complement(operator_)

        operand = rule.get("operand", None)

        if operand is not None and not isinstance(operand, self._operand_types):
            raise RuleError("unallowed operand type: {}".format(type(operand)))

        self._getter = getter
        self._rule = rule
        self._key = key
        self._opcode = opcode
        self._invert = invert
        self._operator = operator_
        self._operand = operand

    def _get_relevance_level(self, item):
        value = self._get_value(item)

        if not isinstance(value, self._value_types):
            return RelevanceLevel.inapplicable

        relevance_level = RelevanceLevel.type_matching

        if self._keys:
            relevance_level |= RelevanceLevel.key_matching

        return relevance_level

    def get_relevance_level(self, item):
        return self._get_relevance_level(item)

    def check(self, item):
        value = self._get_value(item)
        operand = self._operand

        if operand is None:
            operand = self._get_default_value(value)

        return self._operator(value, operand)

    def _get_value(self, item):
        return self._getter(item, self._key)

    def _get_default_value(self, value):
        if value is None:
            return None

        return value.__class__()


class RuleNumeric(RuleBase):

    _operators = {
        "equal":            operator.eq,
        "greater":          operator.gt,
        "greater_or_equal": operator.ge,
        "less":             operator.lt,
        "less_or_equal":    operator.le,
    }
    _aliases = {
        "eq":     "equal",
        "is":     "equal",
        "ne":     "not_equal",
        "is_not": "not_equal",
        "gt":     "greater",
        "gte":    "greater_or_equal",
        "ge":     "greater_or_equal",
        "lt":     "less",
        "lte":    "less_or_equal",
        "le":     "less_or_equal",
    }

    _operand_types = integer_types + (float,)
    _value_types   = integer_types + (float,)


class RuleListBase(RuleBase):

    def __init__(self, rule, getter):
        super(RuleListBase, self).__init__(rule, getter)

        ignore_case = self._rule.get("ignore_case", False)

        if ignore_case:
            self._operand = self._to_lower(self._operand)
            self._operator = self._ignore_case_wrapper(self._operator)

        self._ignore_case = ignore_case

    @classmethod
    def _ignore_case_wrapper(cls, operator_):
        to_lower = cls._to_lower
        return lambda value, operand: operator_(to_lower(value), operand)

    @classmethod
    def _to_lower(cls, value, recursive=1):
        if isinstance(value, list):
            if recursive == 0:
                return value

            return [cls._to_lower(v, recursive - 1) for v in value]

        if isinstance(value, string_types):
            return value.lower()

        return value


class RuleListAsValue(RuleListBase):

    _operators = {
        "equal":            operator.eq,
        "greater":          operator.gt,
        "greater_or_equal": operator.ge,
        "less":             operator.lt,
        "less_or_equal":    operator.le,
        "empty":            lambda value, operand: isempty(value),
        "contains":         operator.contains,  # NOTE: contains(collection, value)

    }
    _aliases = {
        "eq":      "equal",
        "is":      "equal",
        "ne":      "not_equal",
        "is_not":  "not_equal",
        "gt":      "greater",
        "gte":     "greater_or_equal",
        "ge":      "greater_or_equal",
        "lt":      "less",
        "lte":     "less_or_equal",
        "le":      "less_or_equal",
        "include": "contains",
    }

    _value_types = (tuple, list, )


class RuleListAsOperand(RuleListBase):

    _operators = {
        "in": lambda value, operand: operator.contains(operand, value)
    }

    _operand_types = (tuple, list, )


class RuleString(RuleBase):

    _operators = {
        "empty":      lambda value, operand: isempty(value),
        "equal":      operator.eq,
        "contains":   lambda value, operand: operand in value,
        "in":         lambda value, operand: value in operand,
        "startswith": lambda value, operand: value.startswith(operand),
        "endswith":   lambda value, operand: value.endswith(operand),
    }
    _aliases = {
        "eq":     "equal",
        "is":     "equal",
        "ne":     "not_equal",
        "is_not": "not_equal",
        "starts": "startswith",
        "ends":   "endswith",
    }

    _operand_types = (string_types, )
    _value_types   = (string_types, )

    def __init__(self, rule, getter):
        super(RuleString, self).__init__(rule, getter)

        ignore_case = self._rule.get("ignore_case", False)

        if ignore_case:
            self._operand  = self._operand.lower()
            self._operator = self._ignore_case_wrapper(self._operator)

        self._ignore_case = ignore_case

    @classmethod
    def _ignore_case_wrapper(cls, operator_):
        return lambda value, operand: operator_(value.lower(), operand)


class RuleRegex(RuleBase):

    _operators = {
        "regex_match":  lambda value, operand: operand.match(value) is not None,
        "regex_search": lambda value, operand: operand.search(value) is not None,
    }
    _aliases = {
        "match":  "regex_match",
        "regex":  "regex_search",
        "search": "regex_search",
    }

    _operand_types = (string_types, )
    _value_types   = (string_types, )

    def __init__(self, rule, getter):
        super(RuleRegex, self).__init__(rule, getter)

        ignore_case = self._rule.get("ignore_case", False)
        flags = re.U

        if ignore_case:
            flags |= re.I

        self._operand = re.compile(self._operand, flags)
        self._ignore_case = ignore_case
        self._flags = flags


class PatternSyntaxError(RuleError):
    pass


class RulePattern(RuleBase):

    _operators = {
        "pattern_match": lambda value, operand: operand.search(value) is not None,
    }

    _operand_types = (string_types, )
    _value_types   = (string_types, )

    def __init__(self, rule, getter):
        super(RulePattern, self).__init__(rule, getter)

        ignore_case = self._rule.get("ignore_case", False)
        flags = re.U

        if ignore_case:
            flags |= re.I

        self._operand = re.compile(
            self._parse_operand(self._operand), flags)
        self._ignore_case = ignore_case
        self._flags = flags

    @staticmethod
    def _get_regex(pattern):
        result = [r"\b"]
        is_char_set = False
        char_set = []
        escaped = False

        for c in pattern:
            if escaped:
                result.append(re.escape(c))
                escaped = False

            elif c == "\\":
                escaped = True

            elif is_char_set:
                if escaped:
                    char_set.append("\\")
                    char_set.append(c)

                elif c == "]":
                    result.extend(char_set)
                    result.append(c)
                    char_set = []
                    is_char_set = False

                else:
                    char_set.append(c)

            elif c == "[":
                result.append(c)
                is_char_set = True
                char_set = []

            elif c == "?":
                result.append(r".")

            elif c == "*":
                result.append(r"\w*")

            else:
                result.append(re.escape(c))

        if escaped:
            raise PatternSyntaxError("single backslash cannot terminate word pattern")

        if is_char_set:
            raise PatternSyntaxError("char set is not closed")

        result.append(r"\b")

        return "".join(result)

    @classmethod
    def _parse_operand(cls, operand):
        parts = []
        patterns = re.split(r"\s+", operand, re.U)

        for pattern in patterns[:-1]:
            pattern = pattern.strip()

            if not pattern:
                continue

            if pattern.startswith("{"):
                if not re.match(r"\{(?:\d+|\d+,|,\d+|\d+,\d+)\}", pattern, re.U):
                    raise PatternSyntaxError("'{}' is not valid metachar".format(pattern))

                parts.append(r"(?:\b\w+\b\W+)")
                parts.append(pattern)

            else:
                parts.append(cls._get_regex(pattern))
                parts.append(r"\W+")

        pattern = patterns[-1]

        if pattern.startswith("{"):
            raise PatternSyntaxError("{x,y} metachar cannot terminate pattern")

        parts.append(cls._get_regex(pattern))

        return "".join(parts)


class RuleDateTimeBase(RuleBase):

    _operators = {
        "equal":            operator.eq,
        "greater":          operator.gt,
        "greater_or_equal": operator.ge,
        "less":             operator.lt,
        "less_or_equal":    operator.le,
    }
    _aliases = {
        "eq":     "equal",
        "is":     "equal",
        "ne":     "not_equal",
        "is_not": "not_equal",
        "gt":     "greater",
        "gte":    "greater_or_equal",
        "ge":     "greater_or_equal",
        "lt":     "less",
        "lte":    "less_or_equal",
        "le":     "less_or_equal",
    }

    _operand_types = (string_types, datetime.datetime)
    _value_types   = (string_types, datetime.datetime)

    def __init__(self, rule, getter):
        super(RuleDateTimeBase, self).__init__(rule, getter)

        try:
            self.operand = self._parse(self._operand)
        except ValueError:
            raise RuleError("can not parse operand")

        self._last_value  = None
        self._last_parsed_value = None

    def _get_value(self, item):
        value = self._getter(item, self._key)

        if value == self._last_value:
            return self._last_parsed_value

        parsed_value = self._parse(value)
        self._last_value = value
        self._last_parsed_value = parsed_value

        return parsed_value

    def _parse(self, value):
        raise NotImplementedError()

    def get_relevance_level(self, item):
        relevance_level = self._get_relevance_level(item)

        if relevance_level & RelevanceLevel.type_matching:
            relevance_level |= RelevanceLevel.value_matching

        return relevance_level


class RuleDate(RuleDateTimeBase):

    def _parse(self, value):
        if isinstance(value, string_types):
            return datetime.datetime.strptime(value, "%d.%m.%Y")

        return value


class RulesBundle(object):

    def __init__(self, rules):
        super(RulesBundle, self).__init__()

        self._rules = rules

    def check(self, item):
        most_relevant_rule = None
        most_relevant_rule_level = 0
        most_relevant_rule_count = 0

        for rule in self._rules:
            rule_relevance_level = rule.get_relevance_level(item)

            if rule_relevance_level == most_relevant_rule_level:
                most_relevant_rule_count += 1

            elif rule_relevance_level > most_relevant_rule_level:
                most_relevant_rule = rule
                most_relevant_rule_level = rule_relevance_level
                most_relevant_rule_count = 1

        if most_relevant_rule is None:
            raise RuntimeError("can not find any relevant rule")

        if most_relevant_rule_count > 1:
            raise RuntimeError("more than one most relevant rule is found")

        return most_relevant_rule.check(item)


class Filter(object):

    _rules = (
        RuleNumeric,
        RuleListAsValue,
        RuleListAsOperand,
        RuleString,
        RuleRegex,
        RulePattern,
        # RuleDate,
    )

    _default_arguments = {}

    _aliases = {}
    _virtuals = {}
    _defaults = {}

    @staticmethod
    def trafaret():
        return t.Dict({
            t.Key("relation", optional=True): t.Enum("or", "and", "ratio"),
            t.Key("rules"): t.List(
                t.Or(
                    t.Dict({
                        t.Key("key"): t.String | t.List(t.String),
                        t.Key("operator"): t.String,
                        t.Key("operand", optional=True): t.Any,
                        t.Key("default", optional=True): t.Bool,
                        t.Key("invert", optional=True): t.Bool,
                        t.Key("ignore_case", optional=True): t.Bool,
                        t.String: t.Any
                    }),
                    t.List(t.Any, min_length=2),
                ),
                min_length=1
            )
        })

    def __init__(self, source):
        super(Filter, self).__init__()

        self.trafaret().check(source)
        self._rules_instances = []

        for dirty_rule in source["rules"]:
            for rule in self._unfold_rule(dirty_rule):
                for key, value in iteritems(self._default_arguments):
                    rule.setdefault(key, value)

                self._rules_instances.append(self._compile(rule))

        relation = source.get("relation", "or")
        self.check = getattr(self, "_check_{}".format(relation))

    def _check_or(self, item):
        return any(rule.check(item) for rule in self._rules_instances)

    def _check_and(self, item):
        return all(rule.check(item) for rule in self._rules_instances)

    def __call__(self, item):
        return self.check(item)

    @classmethod
    def _unfold_rule(cls, dirty_rule):
        if isinstance(dirty_rule, list):
            dirty_rule = cls._rule_from_list(dirty_rule)

        keys = dirty_rule["key"]

        if not isinstance(keys, list):
            keys = [keys, ]

        rules = []

        for key in keys:
            rule = dict(dirty_rule)
            rule["key"] = key
            rules.append(rule)

        return rules

    @staticmethod
    def _rule_from_list(lst):
        if len(lst) < 2:
            raise ValueError("invalid list rule")

        rule = {
            "key": lst[0],
            "operator": lst[1],
        }

        if len(lst) > 2:
            rule["operand"] = lst[2]

            for key in lst[3:]:
                rule[key] = True

        return rule

    def _compile(self, source):
        instances = []
        errors = []

        for rule_class in self._rules:
            try:
                instances.append(rule_class(source, self._getter))
            except RuleError as e:
                errors.append((rule_class, e))

        if not instances:
            error_text = ["cannot create any rule instance:", ]

            for cls, err in errors:
                error_text.append("{}: {}".format(cls.__name__, err))

            raise ValueError("\n".join(error_text))

        return RulesBundle(instances)

    def _getter(self, item, key):
        key = self._aliases.get(key, key)

        if key in self._virtuals:
            return self._virtuals[key](item)

        Nothing = object()
        value = item
        default = self._defaults

        for k in self._aliases.get(key, key).split("."):
            if default is not Nothing:
                default = default.get(k, Nothing)

            try:
                value = value[k]
            except KeyError:
                if default is Nothing:
                    return self._missing(item, key)

                value = default
                default = Nothing

        return value

    def _missing(self, item, key):
        raise KeyError(key)

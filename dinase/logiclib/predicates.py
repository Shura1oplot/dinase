# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class PredicateCompiler(object):

    def __init__(self, functions=None):
        super(PredicateCompiler, self).__init__()

        self._cur_token = None
        self._cur_name = None
        self._functions = functions or {}
        self._tokens = None

    def __call__(self, expression):
        return self.compile(expression)

    def compile(self, expression):
        self._lex(expression)
        return self._expr()

    def _lex(self, expression):
        self._tokens = []

        for x in expression.split():
            if len(x) == 0:
                continue

            if x == "(":
                self._tokens.append("LP")
                continue

            if x == "(":
                self._tokens.append("LP")
                continue

            while x[0] == "(":
                self._tokens.append("LP")
                x = x[1:]

            RP_count = 0

            while x[-1] == ")":
                RP_count += 1
                x = x[0:-1]

            self._tokens.append(x)

            while RP_count > 0:
                self._tokens.append("RP")
                RP_count -= 1

        self._tokens.reverse()

    def _get_token(self):
        if not self._tokens:
            self._cur_token = "END"
            return

        token = self._tokens.pop()
        token_upper = token.upper()

        if token_upper in ("TRUE", "FALSE", "NOT", "AND", "OR", "LP", "RP"):
            self._cur_token = token_upper

        else:
            self._cur_token = "NAME"
            self._cur_name = token

    def _prim(self):
        self._get_token()

        if self._cur_token == "TRUE":
            self._get_token()
            return self._const_true()

        elif self._cur_token == "FALSE":
            self._get_token()
            return self._const_false()

        elif self._cur_token == "NAME":
            self._get_token()
            return self._functions[self._cur_name]

        elif self._cur_token == "NOT":
            return self._complement(self._prim())

        elif self._cur_token == "LP":
            e = self._expr()

            if self._cur_token != "RP":
                raise ValueError('expected ")"')

            self._get_token()
            return e

        elif self._cur_token == "END":
            # This node is used only if expression is empty
            return self._const_true()

        else:
            raise ValueError("expected primary expression")

    def _term(self):
        left = self._prim()

        while True:
            if self._cur_token == "AND":
                left = self._all(left, self._prim())
            else:
                return left

    def _expr(self):
        left = self._term()

        while True:
            if self._cur_token == "OR":
                left = self._any(left, self._term())
            else:
                return left

    @staticmethod
    def _const_true():
        return lambda *args, **kwargs: True

    @staticmethod
    def _const_false():
        return lambda *args, **kwargs: False

    @staticmethod
    def _complement(function):
        return lambda *args, **kwargs: not function(*args, **kwargs)

    @staticmethod
    def _all(left, right):
        return lambda *args, **kwargs: \
            all(func(*args, **kwargs) for func in (left, right))

    @staticmethod
    def _any(left, right):
        return lambda *args, **kwargs: \
            any(func(*args, **kwargs) for func in (left, right))


def compile(expression, functions=None):  # pylint: disable=W0622
    return PredicateCompiler(functions).compile(expression)

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from . import ru

__all__ = ("translations", )


def create_translation(module):
    return (module.__name__, module.phrases_translation, module.translation)


translations = (
    create_translation(ru),
)

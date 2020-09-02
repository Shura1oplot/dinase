# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import trafaret as t

from dinase.sugar.dict import map_values
from dinase.filterengine.entries import EntryFilter

from .utils import load_json


__all__ = ("filters", )


filters = map_values(
    EntryFilter,
    t.Dict({
        t.String: EntryFilter.t()
    }).check(load_json("filters.json"))
)

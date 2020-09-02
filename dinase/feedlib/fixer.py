# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import hashlib
import re

from dinase.sugar.future import string_types, text_type
from dinase.sugar.dict import iteritems

from .. import datelib


head_detail_fields = {
    "generator": ("name", "href", "version"),
    "info": ("value", "type"),
    "rights": ("value", "type"),
    "subtitle": ("value", "type"),
    "title": ("value", "type"),
}

entry_detail_fields = {
    "summary": ("value", "type"),
    "title": ("value", "type"),
}


def fix_head(head):
    if not head:
        return None

    result = {}

    result.update(_author(head, head))
    result.update(_person(head, "publisher"))

    for name in ("info", "rights", "subtitle"):
        result.update(_detail(head, name))

    result.update(_title(head, "<untitled feed>"))

    result.update(_contributors(head))

    for name in ("icon", "logo"):
        if name in head:
            result[name] = head[name]

    result.update(_links(head))
    result.update(_tags(head))

    result.update(_date(head, "published"))
    result.update(_updated(head))

    result.update(_id(result, head))

    return result


def fix_entries(entries, head, sort=True):
    if not entries:
        return []

    fixed_entries = []

    for entry in entries:
        fixed_entry = fix_entry(entry, head)

        if fixed_entry:
            fixed_entries.append(fixed_entry)

    if sort:
        fixed_entries.sort(key=lambda entry: datelib.xsd.parse(
            entry["updated"]), reverse=True)

    return fixed_entries


def fix_entry(entry, head):
    if not entry:
        return None

    for key in ("id", "link", "title", "summary"):
        if key in entry:
            break
    else:
        return None

    fixed = {}

    fixed.update(_author(entry, head))
    fixed.update(_person(entry, "publisher"))

    fixed.update(_title(entry, "<untitled entry>"))

    fixed.update(_detail(entry, "summary"))

    if "summary" not in fixed:
        if "title" in fixed:
            fixed["summary"] = fixed["title"]

        elif "link" in entry:
            fixed["summary"] = {"value": entry["link"], "type": "text/plain"}

    if "content" in entry:
        fixed_content = []

        for item in entry["content"]:
            value = item.get("value")

            if not value:
                continue

            fixed_item = {"value": value}

            if "type" in item:
                fixed_item["type"] = item["type"]

            fixed_content.append(fixed_item)

        if fixed_content:
            fixed["content"] = fixed_content

    fixed.update(_contributors(entry))
    fixed.update(_links(entry))
    fixed.update(_tags(entry))

    for name in ("created", "expired", "published"):
        fixed.update(_date(entry, name))

    fixed.update(_updated(entry))

    fixed.update(_id(fixed, entry))

    return fixed


def _author(d, h):
    r = _person(d, "author")

    if r:
        return r

    r = _person(d, "publisher")

    if r:
        return {"author": r["publisher"]}

    author = {}

    r = _detail(h, "title")

    if r:
        author["name"] = r["title"]["value"]

    if "link" in h:
        author["href"] = h["link"]

    if author:
        return {"author": author}

    return {"author": {"name": "anonymous"}}


def _person(d, key):
    key_detail = "{}_detail".format(key)

    if key_detail in d:
        item_detail = d[key_detail]

    elif key in d:
        t = d[key]

        if isinstance(t, dict):
            item_detail = t

        elif isinstance(t, string_types):
            item_detail = {"name": t}

        else:
            return {}

    else:
        return {}

    item = _copy(item_detail, ("name", "href", "email"))

    if item:
        return {key: item}

    return {}


def _title(d, default):
    return _detail(d, "title", {
        "value": d.get("link", default),
        "type": "text/plain"}
    )


def _detail(d, key, default=None):
    key_detail = "{}_detail".format(key)

    item_detail = None

    if key_detail in d:
        item_detail = d[key_detail]

    elif key in d:
        t = d[key]

        if isinstance(t, dict):
            item_detail = t

        elif isinstance(t, string_types):
            item_detail = {"value": t}

    if not item_detail:
        return {key: default} if default else {}

    value = item_detail.get("value")

    if not value:
        return {key: default} if default else {}

    result = {"value": value}

    if "type" in item_detail:
        result["type"] = item_detail["type"]

    return {key: result}


def _contributors(d):
    if "contributors" not in d:
        return {}

    contributors = []

    for item in d["contributors"]:
        contributor = _copy(item, ("name", "href", "email"))

        if contributor:
            contributors.append(contributor)

    if contributors:
        return {"contributors": contributors}

    return {}


def _links(d):
    links = []

    for link in d.get("links", []):
        if link["rel"] not in ("alternate", "enclosure", "related", "self", "via"):
            continue

        if "href" not in link:
            continue

        keys = ["rel", "href", "title"]

        if "type" in link and re.match(r"^.+/.+$", link["type"]):
            keys.append("type")

        links.append(_copy(link, keys))

    result = {}

    if "link" in d:
        result["link"] = d["link"]

    if links:
        result["links"] = links

    return result


def _tags(d):
    if "tags" not in d:
        return {}

    tags = []

    for item in d["tags"]:
        tag = _copy(item, ("term", "scheme", "label"))

        if tag:
            tags.append(tag)

    if tags:
        return {"tags": tags}

    return {}


def _date(d, name):
    if name not in d:
        return {}

    value = d[name]

    if not isinstance(value, string_types):
        try:
            value = datelib.xsd.format(datelib.to_datetime(value))
        except ValueError:
            return {}

        return {name: value}

    if datelib.xsd.validate(value):
        return {name: value}

    try:
        value = datelib.xsd.format(datelib.parse(value))
    except ValueError:
        return {}

    return {name: value}


def _updated(d):
    r = _date(d, "updated")

    if r:
        return r

    r = _date(d, "published")

    if r:
        return {"updated": r["published"]}

    return {"updated": datelib.xsd.format(datetime.datetime.today())}


def _id(r, d):
    if "id" in d:
        return {"id": d["id"]}

    if "link" in d:
        return {"id": d["link"]}

    fields = []

    for field in ("title", "subtitle", "summary"):
        if field in r:
            fields.append(r[field]["value"])

    if "author" in r:
        author = r["author"]

        for field in ("name", "href", "email"):
            if field in author:
                fields.append(author[field])

    sha1 = hashlib.sha1()

    for field in fields:
        if isinstance(field, text_type):
            field = field.encode("utf-8")

        sha1.update(field)

    return {"id": "urn:sha1:{}".format(sha1.hexdigest())}


def _copy(d, keys):
    return {k: v for k, v in iteritems(d) if k in keys and v}

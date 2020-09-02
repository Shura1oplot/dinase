# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import absolute_import

import sys
import re
import time
import datetime
from urlparse import urljoin

import grab

from dinase.sugar.future import string_types
from dinase.sugar.func import keep

from . import atom
from .fixer import fix_head, fix_entries
from .. import datelib


class HTMLParserBase(object):

    title = None
    subtitle = None
    link = None
    author = None

    entries_xpath = None
    datetime_mask = None

    def __init__(self):
        super(HTMLParserBase, self).__init__()

        self.feed = None
        self.entries = []
        self.grab = grab.Grab()

    def run(self):
        self.create_feed()
        self.parse_web()

        sys.stdout.write("Content-type:application/atom+xml;charset=utf-8\n\n")
        sys.stdout.write(atom.get_xml(self.feed, self.entries))
        sys.stdout.flush()

    def create_feed(self):
        if self.link is None:
            raise ValueError("link is missing")

        if self.title is None:
            raise ValueError("title is missing")

        self.feed = {
            "title": {
                "type": "text/plain",
                "value": self.title
            },
            "links": [
                {
                    "rel": "alternate",
                    "type": "text/html",
                    "href": self.link,
                    "title": self.title
                }
            ],
            "author": {
                "name": self.author or self.title
            }
        }

        if self.subtitle is not None:
            self.feed["subtitle"] = {
                "type": "text/plain",
                "value": self.subtitle
            }

        self.feed = fix_head(self.feed)

    def parse_web(self):
        self.grab.go(self.link)

        for item in self.grab.doc.select(self.entries_xpath):
            self.entries.extend(
                self.create_atom_entry(entry)
                for entry in self.extract_entries(item)
            )

        self.entries = fix_entries(self.entries, self.feed)

    def extract_entries(self, item):
        raise NotImplementedError()

    def create_atom_entry(self, entry):
        atom_entry = {
            "links": [
                {
                    "rel": "alternate",
                    "type": "text/html",
                    "href": urljoin(self.link, entry["link"])
                }
            ],
            "title": {
                "type": "text/plain",
                "value": self.make_title(entry["title"])
            }
        }

        if "id" in entry:
            atom_entry["id"] = entry["id"]

        if "summary" in entry:
            summary = self.make_summary(entry["summary"])

            if summary:
                atom_entry["summary"] = {
                    "type": "text/html" if entry.get("summary_is_html", False)
                            else "text/plain",
                    "value": summary
                }

        if "published" in entry:
            published = entry["published"]

            if isinstance(published, datetime.datetime):
                atom_entry["published"] = self.make_date(published)

            elif isinstance(published, string_types) and self.datetime_mask:
                published = time.strptime(published, self.datetime_mask)

            atom_entry["published"] = self.make_date(published)

        if "author" in entry:
            atom_entry["author"] = {
                "name": entry["author"]
            }

        return atom_entry

    @classmethod
    def make_title(cls, title):
        return cls._normalize_line(title)

    @classmethod
    def make_summary(cls, summary):
        return "\n".join(keep(cls._normalize_line, summary.split("\n")))

    @staticmethod
    def _normalize_line(line):
        line = line.strip()
        line = re.compile(r"[\b\r]+", flags=re.U).sub(r"", line)
        line = re.compile(r" {2,}", flags=re.U).sub(r" ", line)

        return line

    @staticmethod
    def make_date(value):
        if isinstance(value, string_types):
            if datelib.xsd.validate(value):
                return value

            value = datelib.parse(value)

        value = datelib.to_datetime(value)

        return datelib.xsd.format(value)

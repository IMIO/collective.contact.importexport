# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from collective.transmogrifier.utils import Expression
from collective.transmogrifier.utils import openFileReference
from zope.interface import classProvides
from zope.interface import implements

import csv


class CSVContactSourceSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier

        self.organization_filename = options.get('organization_filename')
        self.organization_fieldnames = options.get('organization_fieldnames')
        if self.organization_fieldnames:
            self.organization_fieldnames = self.organization_fieldnames.split()
        self.persons_filename = options.get('persons_filename')
        self.persons_fieldnames = options.get('persons_fieldnames')
        if self.persons_fieldnames:
            self.persons_fieldnames = self.persons_fieldnames.split()
        self.positions_filename = options.get('positions_filename')
        self.positions_fieldnames = options.get('positions_fieldnames')
        if self.positions_fieldnames:
            self.positions_fieldnames = self.positions_fieldnames.split()

        if self.organization_filename is None and self.persons_filename is None:
            raise Exception("You must specify at least organizations or persons CSV")

        self.csv_headers = Condition(options.get('csv_headers', 'python:True'), transmogrifier, name, options)
        self.dialect = options.get('dialect', 'excel')
        self.fmtparam = dict(
            (key[len('fmtparam-'):],
             Expression(value, transmogrifier, name, options)(
                 options, key=key[len('fmtparam-'):])) for key, value
            in options.iteritems() if key.startswith('fmtparam-'))

    def __iter__(self):
        for item in self.previous:
            yield item

        if self.organization_filename:
            bypassed = False
            for item in self.rows(self.organization_filename, self.organization_fieldnames):
                if self.csv_headers and not bypassed:
                    # Bypass CSV headers if any
                    bypassed = True
                    continue
                item["_type"] = "organization"
                yield item

        if self.persons_filename:
            bypassed = False
            for item in self.rows(self.persons_filename, self.persons_fieldnames):
                if self.csv_headers and not bypassed:
                    # Bypass CSV headers if any
                    bypassed = True
                    continue
                item["_type"] = "person"
                yield item

        if self.positions_filename:
            bypassed = False
            for item in self.rows(self.positions_filename, self.positions_fieldnames):
                if self.csv_headers and not bypassed:
                    # Bypass CSV headers if any
                    bypassed = True
                    continue
                item["_type"] = "position"
                yield item

    def rows(self, filename, fieldnames):
        file_ = openFileReference(self.transmogrifier, filename)
        if file_ is None:
            return
        reader = csv.DictReader(
            file_, dialect=self.dialect,
            fieldnames=fieldnames,
            **self.fmtparam)
        for item in reader:
            yield item
        file_.close()

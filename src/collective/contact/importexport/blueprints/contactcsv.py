# -*- coding: utf-8 -*-
from collective.contact.importexport import logger
from collective.contact.importexport.utils import input_error
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from collective.transmogrifier.utils import Expression
from collective.transmogrifier.utils import openFileReference
from Products.CMFPlone.utils import safe_unicode
from zope.interface import classProvides
from zope.interface import implements

import csv


class CSVContactSourceSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier

        self.organizations_filename = safe_unicode(options.get('organizations_filename'))
        if self.organizations_filename:
            self.organization_fieldnames = transmogrifier['config'].get('organizations_fieldnames', '').split()
        self.persons_filename = safe_unicode(options.get('persons_filename'))
        if self.persons_filename:
            self.persons_fieldnames = transmogrifier['config'].get('persons_fieldnames', '').split()
        self.held_positions_filename = safe_unicode(options.get('held_positions_filename'))
        if self.held_positions_filename:
            self.held_positions_fieldnames = transmogrifier['config'].get('held_positions_fieldnames', '').split()

        if self.organizations_filename is None and self.persons_filename is None:
            raise Exception('You must specify at least organizations or persons CSV')

        self.csv_headers = Condition(options.get('csv_headers', 'python:True'), transmogrifier, name, options)
        self.dialect = safe_unicode(options.get('dialect', 'excel'))
        self.fmtparam = dict(
            (key[len('fmtparam-'):],
             Expression(value, transmogrifier, name, options)(
                 options, key=key[len('fmtparam-'):])) for key, value
            in options.iteritems() if key.startswith('fmtparam-'))

    def __iter__(self):
        for item in self.previous:
            yield item

        if self.organizations_filename:
            for item in self.rows(u'organization', self.organizations_filename, self.organization_fieldnames):
                yield item

        if self.persons_filename:
            for item in self.rows(u'person', self.persons_filename, self.persons_fieldnames):
                yield item

        if self.held_positions_filename:
            for item in self.rows(u'held_position', self.held_positions_filename, self.held_positions_fieldnames):
                yield item

    def rows(self, typ, filename, fieldnames):
        file_ = openFileReference(self.transmogrifier, filename)
        if file_ is None:
            raise Exception("Cannot open file '{}'".format(filename))
        logger.info('Reading {}'.format(filename))
        reader = csv.DictReader(file_, dialect=self.dialect, fieldnames=fieldnames, restkey='_rest',
                                restval='__NO_CO_LU_MN__', **self.fmtparam)
        for item in reader:
            item['_type'] = typ
            item['_ln'] = reader.line_num
            # check fieldnames length on first line
            if reader.line_num == 1:
                reader.restval = u''
                if '_rest' in item:
                    input_error(item, u'STOPPING: some columns are not defined in fieldnames: {}'.format(item['_rest']))
                    break
                extra_cols = [key for (key, val) in item.items() if val == '__NO_CO_LU_MN__']
                if extra_cols:
                    input_error(item, u'STOPPING: to much columns defined in fieldnames: {}'.format(extra_cols))
                    break
                # pass headers if any
                if self.csv_headers:
                    continue
            yield item
        file_.close()

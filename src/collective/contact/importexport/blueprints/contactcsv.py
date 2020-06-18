# -*- coding: utf-8 -*-
from collective.contact.importexport import logger
from collective.contact.importexport.blueprints.main import ANNOTATION_KEY
from collective.contact.importexport.blueprints.main import MANAGED_TYPES
from collective.contact.importexport.utils import input_error
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from collective.transmogrifier.utils import Expression
from collective.transmogrifier.utils import openFileReference
from Products.CMFPlone.utils import safe_unicode
from zope.annotation import IAnnotations
from zope.interface import classProvides
from zope.interface import implements

import csv


class CSVDiskSourceSection(object):
    """ Open disk files from filenames ans store handlers """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        for typ in MANAGED_TYPES:
            filename = safe_unicode(options.get('{}s_filename'.format(typ), ''))
            if filename:
                file_ = openFileReference(transmogrifier, filename)
                if file_ is None:
                    raise Exception("Cannot open file '{}'".format(filename))
                self.storage['csv_files'][typ] = file_
        if self.storage['csv_files']['organization'] is None and self.storage['csv_files']['person'] is None:
            raise Exception('You must specify at least organizations or persons CSV')

    def __iter__(self):
        for item in self.previous:
            yield item


class CSVReaderSection(object):
    """ Read as csv file handlers stored in self.storage['csv_files'][typ] """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
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

        for typ in MANAGED_TYPES:
            if self.storage['csv_files'][typ] is None:
                continue
            for item in self.rows(typ):
                yield item

    def rows(self, typ):
        logger.info(u"Reading '{}' csv file".format(typ))
        reader = csv.DictReader(self.storage['csv_files'][typ], dialect=self.dialect,
                                fieldnames=self.storage['fieldnames'][typ], restkey='_rest',
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
        self.storage['csv_files'][typ].close()

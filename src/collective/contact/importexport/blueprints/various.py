# -*- coding: utf-8 -*-

from collective.contact.importexport.blueprints.main import e_logger
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from zope.annotation.interfaces import IAnnotations
from zope.interface import classProvides
from zope.interface import implements

import ipdb
import os
import sys


class AddCounter(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.keyname = options.get('keyname', '_counter')
        self.firstvalue = options.get('firstvalue', 1)

    def __iter__(self):
        counter = self.firstvalue
        for item in self.previous:
            item[self.keyname] = counter
            counter += 1
            yield item


class BreakpointSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        condition = options['condition']
        self.condition = Condition(condition, transmogrifier, name, options)
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                ipdb.set_trace(sys._getframe().f_back)  # Break!
            yield item


class CsvFirstLine(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.section = options.get('section')
        if self.section is None:
            raise Exception("'section' option is required for '{}' section ".format(name))
        if self.section not in transmogrifier:
            raise Exception("'{}' value of '{}' section option is not an existing section".format(name, self.section))
        self.fieldnames = transmogrifier[self.section].get('fieldnames', '')
        filepath = transmogrifier[self.section].get('filename', '')

        self.storage = IAnnotations(transmogrifier).setdefault('csv',
                                                               {'filepath': filepath,
                                                                'filename': os.path.basename(filepath),
                                                                'fields': {}})
        e_logger.info("WORKING on {}".format(self.storage['filename']))

    def __iter__(self):
        for item in self.previous:
            if item['_c'] == 1:
                for fld in self.fieldnames.split():
                    self.storage['fields'][fld] = item[fld]
                continue
            yield item

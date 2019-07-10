# -*- coding: utf-8 -*-

from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from zope.interface import classProvides
from zope.interface import implements

import ipdb
import sys


class AddCounter(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.keyname = options.get('keyname', '_counter')

    def __iter__(self):
        counter = 0
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

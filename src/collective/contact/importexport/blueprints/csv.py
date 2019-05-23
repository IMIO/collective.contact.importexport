# -*- coding: utf-8 -*-

from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from zope.interface import classProvides
from zope.interface import implements


class CSVCleaner(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.remove_header = options.get('remove-header', 'true') == 'true' and True or False

    def __iter__(self):
        if self.remove_header:
            next(self.previous)
        for item in self.previous:
            yield item

# -*- coding: utf-8 -*-

from collective.contact.importexport.blueprints.main import ANNOTATION_KEY
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from zope.annotation.interfaces import IAnnotations
from zope.interface import classProvides
from zope.interface import implements

import ipdb
import sys


class BreakpointSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        condition = options['condition']
        self.condition = Condition(condition, transmogrifier, name, options)
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)

    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
#                ipdb.set_trace(sys._getframe().f_back)  # Break!
                ipdb.set_trace()  # Break!
            yield item

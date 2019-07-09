# -*- coding: utf-8 -*-

from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from zope.annotation.interfaces import IAnnotations
from zope.interface import classProvides
from zope.interface import implements
import logging
logger = logging.getLogger('transmo')
logger.setLevel(20)
for handler in logging.root.handlers:
    if handler.level == 30 and handler.formatter is not None:
        handler.level = 20
        break


class Source1(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.name = name
        self.source_list = options.get('source-list', '').split()
        self.storage = IAnnotations(transmogrifier).setdefault('source1', {})
        logger.info('{0} init'.format(name))

    def __iter__(self):
        logger.info('{0} before previous loop'.format(self.name))
        for item in self.previous:
            logger.info('{0} yield previous'.format(self.name))
            yield item
        logger.info('{0} after previous loop'.format(self.name))
        for elem in self.source_list:
            logger.info('{0} yield elem'.format(self.name))
            yield elem
        logger.info('{0} after elem loop'.format(self.name))


class Source2(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.name = name
        self.source_list = options.get('source-list', '').split()
        self.storage = IAnnotations(transmogrifier).get('source1')
        logger.info('{0} init'.format(name))

    def __iter__(self):
        logger.info('{0} before previous loop'.format(self.name))
        for item in self.previous:
            logger.info('{0} yield previous'.format(self.name))
            yield item
        logger.info('{0} after previous loop'.format(self.name))
        for elem in self.source_list:
            logger.info('{0} yield elem'.format(self.name))
            yield elem
        logger.info('{0} after elem loop'.format(self.name))


class Constructor1(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.name = name
        logger.info('{0} init'.format(name))

    def __iter__(self):
        logger.info('{0} before previous loop'.format(self.name))
        for item in self.previous:
            logger.info('{0} yield previous'.format(self.name))
            yield item
        logger.info('{0} after previous loop'.format(self.name))


class Constructor2(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.name = name
        logger.info('{0} init'.format(name))

    def __iter__(self):
        logger.info('{0} before previous loop'.format(self.name))
        for item in self.previous:
            logger.info('{0} yield previous'.format(self.name))
            yield item
        logger.info('{0} after previous loop'.format(self.name))


"""
Results:
--------
source1 init
source2 init
constructor1 init
constructor2 init
constructor2 before previous loop
constructor1 before previous loop
source2 before previous loop
source1 before previous loop
source1 after previous loop
source1 yield elem
source2 yield previous
constructor1 yield previous
constructor2 yield previous
source1 yield elem
source2 yield previous
constructor1 yield previous
constructor2 yield previous
source1 yield elem
source2 yield previous
constructor1 yield previous
constructor2 yield previous
source1 after elem loop
source2 after previous loop
source2 yield elem
constructor1 yield previous
constructor2 yield previous
source2 yield elem
constructor1 yield previous
constructor2 yield previous
source2 yield elem
constructor1 yield previous
constructor2 yield previous
source2 after elem loop
constructor1 after previous loop
constructor2 after previous loop
"""

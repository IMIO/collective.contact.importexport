# -*- coding: utf-8 -*-

from collective.contact.importexport.utils import get_main_path
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from zope.interface import classProvides
from zope.interface import implements

import logging
import os

e_logger = logging.getLogger('ccie-transmo')


class Initialization(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.workingpath = get_main_path(options.get('basepath', ''), options.get('subpath', ''))
        lfh = logging.FileHandler(os.path.join(self.workingpath, 'ie.log'), mode='w')
        lfh.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        lfh.setLevel(logging.WARN)
        e_logger.addHandler(lfh)

    def __iter__(self):
        for item in self.previous:
            yield item


class OrderOrganizations(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            yield item

class CheckData(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            yield item

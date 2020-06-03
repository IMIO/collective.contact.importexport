# -*- coding: utf-8 -*-

from collective.contact.importexport.utils import get_main_path
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from zope.annotation.interfaces import IAnnotations
from zope.interface import classProvides
from zope.interface import implements

import logging
import os

logger = logging.getLogger('ccie')
e_logger = logging.getLogger('ccie-input')
e_logger.setLevel(logging.INFO)

ANNOTATION_KEY = "collective.contact.importexport"


def input_error(item, msg):
    e_logger.error(u'{}: ln {:d}, {}'.format(item['_type'], item['_ln'], msg))


class Initialization(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.workingpath = get_main_path(options.get('basepath', ''), options.get('subpath', ''))
        lfh = logging.FileHandler(os.path.join(self.workingpath, 'ie_input_errors.log'), mode='w')
        lfh.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        lfh.setLevel(logging.INFO)
        e_logger.addHandler(lfh)
        self.storage = IAnnotations(transmogrifier).setdefault(ANNOTATION_KEY, {})
        self.organizations_ids = self.storage.setdefault("organizations_ids", {})
        self.persons_ids = self.storage.setdefault("persons_ids", {})
        self.positions_ids = self.storage.setdefault("positions_ids", {})

    def __iter__(self):
        for item in self.previous:
            yield item

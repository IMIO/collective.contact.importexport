# -*- coding: utf-8 -*-

from __future__ import print_function
from collective.contact.importexport import A_S
from collective.contact.importexport import o_logger
from collective.contact.importexport import T_S
from collective.contact.importexport.blueprints.main import ANNOTATION_KEY
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from imio.helpers.transmogrifier import key_val as shortcut
from zope.annotation.interfaces import IAnnotations
from zope.interface import classProvides
from zope.interface import implements

import ipdb
# import sys


class BreakpointSection(object):
    """Stops with ipdb if condition is matched.

    Parameters:
        * condition = M, matching condition.
    """
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
                # ipdb.set_trace(sys._getframe().f_back)  # Break!
                ipdb.set_trace()  # Break!
            yield item


class ShortLog(object):
    """Logs shortly item."""
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)

    def __iter__(self):
        for item in self.previous:
            to_print = u"{}:{},{},{}, {}".format(item['_set'], shortcut(item['_type'], T_S), item.get('_id', ''),
                                                 shortcut(item['_act'], A_S),
                                                 item.get('_path', item.get('_del_path', '')))
            # print(to_print, file=sys.stderr)
            o_logger.info(to_print)
            yield item


class StopSection(object):
    """Stops if condition is matched.

    Parameters:
        * condition = M, matching condition.
    """
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
                raise Exception('STOP requested')
            yield item

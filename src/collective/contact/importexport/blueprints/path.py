# -*- coding: utf-8 -*-

from collective.contact.importexport.blueprints.main import ANNOTATION_KEY
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from plone.i18n.normalizer.interfaces import IIDNormalizer
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.interface import classProvides
from zope.interface import implements


class PathInserter(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.title_key = options.get('title-key', 'title')
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.directory_path = self.storage['directory_path']

    def __iter__(self):
        idnormalizer = getUtility(IIDNormalizer)
        for item in self.previous:
            if '_path' in item:
                yield item
                continue
            title = item.get(self.title_key, None)
            if not title:
                continue
            new_id = idnormalizer.normalize(title)
            item["_path"] = '/'.join([self.directory_path, new_id])
            yield item

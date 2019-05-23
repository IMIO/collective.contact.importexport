# -*- coding: utf-8 -*-

from collective.contact.importexport.utils import safe_encode
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from plone import api
from plone.i18n.normalizer.interfaces import IIDNormalizer
from zope.component import getUtility
from zope.interface import classProvides
from zope.interface import implements


class PathInserter(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.directory_path = ""
        brains = api.content.find(portal_type="directory")
        if brains:
            portal_path = '/'.join(api.portal.get().getPhysicalPath())
            self.directory_path = brains[0].getPath().lstrip(portal_path)

    def __iter__(self):
        idnormalizer = getUtility(IIDNormalizer)
        for item in self.previous:
            title = item.get('nom_court', None)
            if not title:
                continue
            new_id = idnormalizer.normalize(safe_encode(title))
            item["_path"] = '/'.join([self.directory_path, new_id])
            yield item

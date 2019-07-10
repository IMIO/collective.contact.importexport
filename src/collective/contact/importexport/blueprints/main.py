# -*- coding: utf-8 -*-

from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from zope.interface import classProvides
from zope.interface import implements


class OrderOrganizations(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            yield item

class CheckDataSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            for col in item
                col = col.strip()
            if not isdigit(item['zipcode']):
                # On doit écrire dans un fichier qu'un élément de la ligne n'est pas conforme
                continue
            yield item

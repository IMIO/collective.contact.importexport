# -*- coding: utf-8 -*-

from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from zope.interface import classProvides
from zope.interface import implements


class DependencySorter(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

    def __iter__(self):
        all_organizations = []
        all_persons = []
        all_held_positions = []
        parent_relation = {}
        for item in self.previous:
            if item["_type"] == "organization":
                if item["_pid"]:
                    parent_relation[item["_oid"]] = item["_pid"]
                all_organizations.append(item)
            elif item["_type"] == "person":
                all_persons.append(item)
            elif item["_type"] == "held_position":
                all_held_positions.append(item)

        for org in all_organizations:
            org["level"] = self.get_level(parent_relation, org["_oid"])
        sorted_organizations = sorted(all_organizations, key=lambda item: (item['level'], item['_oid']))
        for org in sorted_organizations:
            yield org

        for pers in all_persons:
            yield pers

        for pos in all_held_positions:
            yield pos

    def get_level(self, parent_relation, oid):
        return len(self.ancestors(parent_relation, oid))

    def ancestors(self, parent_relation, oid):
        return (self.ancestors(parent_relation, parent_relation[oid]) if oid in parent_relation else []) + [oid]

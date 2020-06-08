# -*- coding: utf-8 -*-

from collective.contact.importexport import logger
from collective.contact.importexport.blueprints.main import ANNOTATION_KEY
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from zope.annotation.interfaces import IAnnotations
from zope.interface import classProvides
from zope.interface import implements


class DependencySorter(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.dir_org_config = self.storage['dir_org_config']
        self.dir_org_config_len = self.storage['dir_org_config_len']
        self.directory_path = self.storage['directory_path']

    def __iter__(self):
        all_organizations = []
        all_persons = []
        all_held_positions = []
        parent_relation = {}
        for item in self.previous:
            # we set None if value is empty string
            for fld in item:
                if item[fld] != u'' or fld.startswith('_') or fld in ('description',):
                    continue
                item[fld] = None
            if item['_type'] == 'organization':
                if item['_pid']:
                    parent_relation[item['_id']] = item['_pid']
                all_organizations.append(item)
            elif item['_type'] == 'person':
                all_persons.append(item)
            elif item['_type'] == 'held_position':
                all_held_positions.append(item)

        for org in all_organizations:
            org['_level'] = self.get_level(parent_relation, org['_id'])
        sorted_organizations = sorted(all_organizations, key=lambda item: (item['_level'], item['_id']))

        # updating directory options
        fields = {}
        for typ in ['types', 'levels']:
            if len(self.dir_org_config[typ]) != self.dir_org_config_len[typ]:
                logger.info("Contacts parameter modification 'organization_%s'" % typ)
            fields['organization_%s' % typ] = [{'name': i[0], 'token': i[1]} for i in self.dir_org_config[typ].items()]
        if fields:
            fields['_path'] = self.directory_path
            fields['_type'] = 'directory'  # to avoid message from constructor
            yield fields

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

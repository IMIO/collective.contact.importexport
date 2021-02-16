# -*- coding: utf-8 -*-

from collective.contact.importexport import logger
from collective.contact.importexport.blueprints.main import ANNOTATION_KEY
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from zope.annotation.interfaces import IAnnotations
from zope.interface import classProvides
from zope.interface import implements


class DependencySorter(object):
    """Sorts organizations by hierarchy.

    * Sets to None empty values.
    * Updates directory if necessary.
    * yields again all items by set.
    """
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
        all_organizations = {}
        all_persons = {}
        all_held_positions = {}
        parent_relation = {}
        sorted_orgs = {}

        for item in self.previous:
            if item['_set'] not in all_organizations:
                all_organizations[item['_set']] = []
                all_persons[item['_set']] = []
                all_held_positions[item['_set']] = []
                parent_relation[item['_set']] = {}
                sorted_orgs[item['_set']] = []
            # we set None if value is empty string
            for fld in item:
                if item[fld] != u'' or fld.startswith('_') or fld in ('description',):
                    continue
                item[fld] = None
            if item['_type'] == 'organization':
                if item['_oid']:
                    parent_relation[item['_set']][item['_id']] = item['_oid']
                all_organizations[item['_set']].append(item)
            elif item['_type'] == 'person':
                all_persons[item['_set']].append(item)
            elif item['_type'] == 'held_position':
                all_held_positions[item['_set']].append(item)

        for sett in all_organizations:
            for org in all_organizations[sett]:
                org['_level'] = self.get_level(parent_relation[sett], org['_id'])
            sorted_orgs[sett] = sorted(all_organizations[sett], key=lambda itom: (itom['_level'], itom['_ln']))

        # updating directory options
        fields = {}
        for typ in ['types', 'levels']:
            if len(self.dir_org_config[typ]) != self.dir_org_config_len[typ]:  # dic updated in CommonInputChecks
                logger.info("Contacts parameter modification 'organization_%s'" % typ)
                fields['organization_%s' % typ] = [{'name': i[0], 'token': i[1]} for i
                                                   in self.dir_org_config[typ].items()]
        if fields:
            fields['_path'] = self.directory_path
            fields['_type'] = 'directory'  # to avoid message from constructor
            fields['_act'] = 'update'
            fields['_set'] = 'all'  # part of printing
            yield fields

        for sett in sorted(all_organizations.keys()):
            for org in sorted_orgs[sett]:
                yield org

            for pers in all_persons[sett]:
                yield pers

            for pos in all_held_positions[sett]:
                yield pos

    def get_level(self, parent_relation, oid):
        return len(self.ancestors(parent_relation, oid))

    def ancestors(self, parent_relation, oid):
        return (self.ancestors(parent_relation, parent_relation[oid]) if oid in parent_relation else []) + [oid]

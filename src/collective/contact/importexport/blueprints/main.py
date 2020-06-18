# -*- coding: utf-8 -*-

from collections import OrderedDict
from collective.contact.importexport import e_logger
from collective.contact.importexport import o_logger
from collective.contact.importexport.utils import alphanum
from collective.contact.importexport.utils import by3wise
from collective.contact.importexport.utils import correct_path
from collective.contact.importexport.utils import get_main_path
from collective.contact.importexport.utils import input_error
from collective.contact.importexport.utils import relative_path
from collective.contact.importexport.utils import valid_date
from collective.contact.importexport.utils import valid_email
from collective.contact.importexport.utils import valid_phone
from collective.contact.importexport.utils import valid_value_in_list
from collective.contact.importexport.utils import valid_zip
from collective.contact.importexport.utils import to_bool
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone import api
from Products.CMFPlone.utils import safe_unicode
from z3c.relationfield.relation import RelationValue
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.interface import classProvides
from zope.interface import implements
from zope.intid.interfaces import IIntIds

import logging
import os

ANNOTATION_KEY = 'collective.contact.importexport'
MANAGED_TYPES = ['organization', 'person', 'held_position']


class Initialization(object):
    """ Initialize global variables to be used in next sections """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.workingpath = get_main_path(safe_unicode(options.get('basepath', '')),
                                         safe_unicode(options.get('subpath', '')))
        self.portal = transmogrifier.context
        lfh = logging.FileHandler(os.path.join(self.workingpath, 'ie_input_errors.log'), mode='w')
        lfh.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        lfh.setLevel(logging.INFO)
        e_logger.addHandler(lfh)
        lfh = logging.FileHandler(os.path.join(self.workingpath, 'ie_shortlog.log'), mode='w')
        lfh.setFormatter(logging.Formatter('%(message)s'))
        lfh.setLevel(logging.INFO)
        o_logger.addHandler(lfh)

        # set global variables in annotation
        self.storage = IAnnotations(transmogrifier).setdefault(ANNOTATION_KEY, {})
        self.storage['ids'] = {typ: {} for typ in MANAGED_TYPES}
#        self.storage['uniques'] = {typ: {} for typ in MANAGED_TYPES}
        self.storage['csv_files'] = {typ: None for typ in MANAGED_TYPES}
        self.storage['fieldnames'] = {typ: transmogrifier['config'].get('{}s_fieldnames'.format(typ), '').split()
                                      for typ in MANAGED_TYPES}
        # find directory
        directory = None
        dir_path = transmogrifier['config'].get('directory_path', '')
        if dir_path:
            dir_path = dir_path.lstrip('/')
            directory = self.portal.unrestrictedTraverse(dir_path, default=None)
        else:
            brains = api.content.find(portal_type='directory')
            if brains:
                directory = brains[0].getObject()
                dir_path = relative_path(self.portal, brains[0].getPath())
        if not directory:
            raise Exception("{}: Directory not found !".format(name))
        self.storage['directory'] = directory
        self.storage['directory_path'] = dir_path
        # store directory configuration
        dir_org_config = {}
        dir_org_config_len = {}
        for typ in ['types', 'levels']:
            dir_org_config[typ] = OrderedDict([(safe_unicode(t['name']), safe_unicode(t['token'])) for t in
                                               getattr(self.storage['directory'], 'organization_%s' % typ)])
            if not len(dir_org_config[typ]):
                dir_org_config[typ] = OrderedDict([(u'Non défini', u'non-defini')])
            dir_org_config_len[typ] = len(dir_org_config[typ])
        self.storage['dir_org_config'] = dir_org_config
        self.storage['dir_org_config_len'] = dir_org_config_len

    def __iter__(self):
        for item in self.previous:
            yield item


class CommonInputChecks(object):
    """ Check input values """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.fieldnames = self.storage['fieldnames']
        self.ids = self.storage['ids']
        self.csv_encoding = transmogrifier['config'].get('csv_encoding', 'utf8')
        self.phone_country = safe_unicode(options.get('phone_country', 'BE')).upper()
        self.language = safe_unicode(options.get('language', 'fr')).lower()
        self.uniques = {typ: {key: {} for key in safe_unicode(options.get('{}_uniques'.format(typ), '')).split()
                              if key in self.fieldnames[typ]}
                        for typ in MANAGED_TYPES}
        self.booleans = {typ: [key for key in safe_unicode(options.get('{}_booleans'.format(typ), '')).split()
                               if key in self.fieldnames[typ]]
                         for typ in MANAGED_TYPES}
        self.storage['booleans'] = self.booleans
        self.dir_org_config = self.storage['dir_org_config']
        self.directory_path = self.storage['directory_path']

    def __iter__(self):
        idnormalizer = getUtility(IIDNormalizer)
        for item in self.previous:
            item_type = item['_type']

            # set correct values
            for fld in self.fieldnames[item_type]:
                item[fld] = safe_unicode(item[fld].strip(' '), encoding=self.csv_encoding)

            if item_type == 'held_position':
                item['_fid'] = None  # we don't yet manage position

            # set directory as default parent
            item['_parent'] = self.directory_path

            # duplicated _id ?
            if not item['_id']:
                input_error(item, u"SKIPPING: missing id '_id'")
                continue
            if item['_id'] in self.ids[item_type]:
                input_error(item, u"duplicated id '{}', already present line {}".format(item['_id'],
                                  self.ids[item_type][item['_id']]['ln']))
            self.ids[item_type][item['_id']] = {'path': '', 'ln': item['_ln']}

            # uniqueness
            for key in self.uniques[item_type]:
                if item[key] in self.uniques[item_type][key]:
                    input_error(item, u"duplicated {} '{}', already present line {:d}".format(key, item[key],
                                      self.uniques[item_type][key][item[key]]))
                elif item[key]:
                    self.uniques[item_type][key][item[key]] = item['_ln']

            # to bool from int
            for key in self.booleans[item_type]:
                item[key] = to_bool(item, key)

            # check zip
            item['zip_code'] = valid_zip(item, 'zip_code', 'country')

            # check phones
            for key in ('phone', 'cell_phone', 'fax'):
                item[key] = valid_phone(item, key, 'country', self.phone_country, self.language)

            # check email
            item['email'] = valid_email(item, 'email')

            # organization checks
            if item_type == 'organization':
                if item['_id'] == item['_oid']:
                    input_error(item, u'SKIPPING: _oid is equal to _id {}'.format(item['_id']))
                    continue
                # keep only alphanum chars
                if 'enterprise_number' in item and item['enterprise_number']:
                    item['enterprise_number'] = alphanum(item['enterprise_number']).strip()
                # manage org type if 'organization_type' column is defined
                # (some clients use this column to put something else)
                if 'organization_type' in item:
                    type_type = item['_oid'] and 'levels' or 'types'
                    if item['organization_type']:
                        if item['organization_type'] not in self.dir_org_config[type_type]:
                            self.dir_org_config[type_type][item['organization_type']] = \
                                safe_unicode(idnormalizer.normalize(item['organization_type']))
                        item['organization_type'] = self.dir_org_config[type_type][item['organization_type']]
                    else:  # we take the first value
                        item['organization_type'] = self.dir_org_config[type_type].values()[0]
            elif item_type == 'person':
                item['gender'] = valid_value_in_list(item, item['gender'], ('', 'F', 'M'))
                item['birthday'] = valid_date(item, item['birthday'])
            elif item_type == 'held_position':
                item['start_date'] = valid_date(item, item['start_date'])
                item['end_date'] = valid_date(item, item['end_date'])
                if not item['_pid']:
                    input_error(item, u"SKIPPING: missing related person id")
                    continue
                if not item['_oid'] and not item['_fid']:
                    input_error(item, u"SKIPPING: missing organization/position id")
                    continue

            yield item


class RelationsInserter(object):
    """ Add relations between objects """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.portal = transmogrifier.context
        self.catalog = self.portal.portal_catalog
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.ids = self.storage['ids']

    def __iter__(self):
        intids = getUtility(IIntIds)
        for item in self.previous:
            item_type = item['_type']
            if item_type == 'held_position':
                if item['_oid'] and item['_oid'] not in self.ids['organization']:
                    input_error(item, u"SKIPPING: invalid related organization id '{}'".format(item['_oid']))
                    continue
                # not using _pid yet
                org = self.portal.unrestrictedTraverse(self.ids['organization'][item['_oid']]['path'])
                item['position'] = RelationValue(intids.getId(org))
            yield item


class UpdatePathInserter(object):
    """ Add _path if we have to do an element update """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.portal = transmogrifier.context
        self.catalog = self.portal.portal_catalog
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.ids = self.storage['ids']
        # we add in options the following information, used in imio.dms.mail context
        cbin = self.portal.portal_quickinstaller.isProductInstalled('collective.behavior.internalnumber')
        # TODO : MUST CHECK IF BEHAVIOR IS WELL ADDED ON PORTAL_TYPE !!
        options['cbin'] = str(cbin)
        self.uniques = {}
        for typ in MANAGED_TYPES:
            values = safe_unicode(options.get('{}_uniques'.format(typ), '')).strip().split()
            if len(values) % 3:
                raise Exception("The '{}' section '{}' option must contain a multiple of 3 elements".format(name,
                                '{}_uniques'.format(typ)))
            self.uniques[typ] = [(f, i, Condition(c, transmogrifier, name, options)) for f, i, c in by3wise(values)]

    def __iter__(self):
        for item in self.previous:
            if '_path' in item:  # _path has already be set
                yield item
                continue
            item_type = item['_type']
            # we will do a search for each index
            for field, idx, condition in self.uniques[item_type]:
                if item[field] and condition(item):
                    brains = self.catalog.unrestrictedSearchResults({'portal_type': item_type, idx: item[field]})
                    if len(brains) > 1:
                        input_error(item, u"the search with '{}'='{}' get multiple objs: {}".format(idx, item[field],
                                          u', '.join([b.getPath() for b in brains])))
                    elif len(brains):
                        item['_path'] = relative_path(self.portal, brains[0].getPath())
                        item['_act'] = 'update'
                        # we store _path for each _id
                        self.ids[item_type][item['_id']]['path'] = item['_path']
                        break
                    else:
                        input_error(item, u"the search with '{}'='{}' get no result".format(idx, item[field]))
            yield item


class PathInserter(object):
    """ Add _path for new element """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.title_keys = safe_unicode(options.get('title-keys', 'title'))
        self.portal = transmogrifier.context
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.fieldnames = self.storage['fieldnames']
        self.ids = self.storage['ids']
        self.id_keys = {typ: [key for key in safe_unicode(options.get('{}_id_keys'.format(typ), '')).split()
                              if key in self.fieldnames[typ]]
                        for typ in MANAGED_TYPES}

    def __iter__(self):
        idnormalizer = getUtility(IIDNormalizer)
        for item in self.previous:
            if '_path' in item:  # _path has already be set
                yield item
                continue
            item_type = item['_type']
            related_title = ''
            title = u'-'.join([item[key] for key in self.id_keys[item_type] if item[key]])

            # organization parent ?
            if item_type in ('organization', 'held_position') and item['_oid']:
                if item['_oid'] not in self.ids['organization']:
                    input_error(item, u"SKIPPING: invalid parent organization id '{}'".format(item['_oid']))
                    continue
                item['_parent'] = self.ids['organization'][item['_oid']]['path']
                related_title = self.portal.unrestrictedTraverse(item['_parent']).get_full_title()
            # person parent ?
            if item_type == 'held_position':
                if item['_pid'] not in self.ids['person']:
                    input_error(item, u"SKIPPING: invalid related person id '{}'".format(item['_pid']))
                    continue
                item['_parent'] = self.ids['person'][item['_pid']]['path']
                if related_title:  # position not taken into account
                    title = u'-'.join([title, related_title])

            if not title:
                input_error(item, u'cannot get an id from id keys {}'.format(self.id_keys[item_type]))
                continue
            new_id = idnormalizer.normalize(title)
            item['_path'] = '/'.join([item['_parent'], new_id])
            # we rename id if it already exists
            item['_path'] = correct_path(self.portal, item['_path'])
            item['_act'] = 'new'
            # we store _path for each _id
            self.ids[item_type][item['_id']]['path'] = item['_path']
            yield item


class TransitionsInserter():
    """ Add _transitions following _inactive column """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.portal = transmogrifier.context
        self.name = name
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.fieldnames = self.storage['fieldnames']
        for typ in MANAGED_TYPES:
            if '_inactive' in self.fieldnames[typ] and not '_inactive' in self.storage['booleans'][typ]:
                raise Exception("{}: _inactive field is not configured as boolean for type {} !".format(self.name, typ))

    def __iter__(self):
        for item in self.previous:
            if '_inactive' in item:
                obj = self.portal.unrestrictedTraverse(item['_path'], default=None)
                state = api.content.get_state(obj=obj)
                if item['_inactive'] and state == 'active':
                    item['_transitions'] = 'deactivate'
                elif not item['_inactive'] and state == 'deactivated':
                    input_error(item, u'_inactive is False and current state is deactivated: we do not activate')
            yield item

# ["{}: '{}'".format(attr, getattr(context, attr)) for attr in ('title', 'description', 'organization_type', 'use_parent_address', 'street', 'number', 'additional_address_details', 'zip_code', 'city', 'phone', 'cell_phone', 'fax', 'email', 'website', 'region', 'country')]

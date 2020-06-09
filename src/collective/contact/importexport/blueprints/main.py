# -*- coding: utf-8 -*-

from collections import OrderedDict
from collective.contact.importexport import e_logger
from collective.contact.importexport.utils import correct_path
from collective.contact.importexport.utils import get_main_path
from collective.contact.importexport.utils import input_error
from collective.contact.importexport.utils import pairwise
from collective.contact.importexport.utils import relative_path
from collective.contact.importexport.utils import valid_email
from collective.contact.importexport.utils import valid_phone
from collective.contact.importexport.utils import valid_zip
from collective.contact.importexport.utils import to_bool
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone import api
from Products.CMFPlone.utils import safe_unicode
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.interface import classProvides
from zope.interface import implements

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
        self.workingpath = get_main_path(options.get('basepath', ''), options.get('subpath', ''))
        lfh = logging.FileHandler(os.path.join(self.workingpath, 'ie_input_errors.log'), mode='w')
        lfh.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        lfh.setLevel(logging.INFO)
        e_logger.addHandler(lfh)

        # set global variables in annotation
        self.storage = IAnnotations(transmogrifier).setdefault(ANNOTATION_KEY, {})
        self.storage['ids'] = {typ: {} for typ in MANAGED_TYPES}
#        self.storage['uniques'] = {typ: {} for typ in MANAGED_TYPES}
        self.storage['fieldnames'] = {typ: transmogrifier['config'].get('{}s_fieldnames'.format(typ), '').split()
                                      for typ in MANAGED_TYPES}
        # find directory
        directory = None
        dir_path = transmogrifier['config'].get('directory_path', '')
        if dir_path:
            dir_path = dir_path.lstrip('/')
            directory = transmogrifier.context.unrestrictedTraverse(dir_path, default=None)
        else:
            brains = api.content.find(portal_type='directory')
            if brains:
                directory = brains[0].getObject()
                dir_path = relative_path(transmogrifier.context, brains[0].getPath())
        if not directory:
            raise Exception("Directory not found !")
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
        self.uniques = {typ: {key: {} for key in options.get('{}_uniques'.format(typ), '').split()
                              if key in self.fieldnames[typ]}
                        for typ in MANAGED_TYPES}
        self.booleans = {typ: {key: {} for key in options.get('{}_booleans'.format(typ), '').split()
                               if key in self.fieldnames[typ]}
                         for typ in MANAGED_TYPES}
        self.dir_org_config = self.storage['dir_org_config']

    def __iter__(self):
        idnormalizer = getUtility(IIDNormalizer)
        for item in self.previous:
            item_type = item['_type']

            # set correct values
            for fld in self.fieldnames[item_type]:
                item[fld] = safe_unicode(item[fld].strip(' '))

            # duplicated _id ?
            if not item['_id'] or item['_id'] in self.ids[item_type]:
                input_error(item, u"missing or duplicated id '{}', already present line {}".format(item['_id'],
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
                item[key] = valid_phone(item, key, 'country')

            # check email
            item['email'] = valid_email(item, 'email')

            # organization checks
            if item_type == 'organization':
                if item['_id'] == item['_pid']:
                    input_error(item, u'SKIPPING: _pid is equal to _id {}'.format(item['_id']))
                    continue
                if item['organization_type']:
                    type_type = item['_pid'] and 'levels' or 'types'
                    if item['organization_type'] not in self.dir_org_config[type_type]:
                        self.dir_org_config[type_type][item['organization_type']] = \
                            safe_unicode(idnormalizer.normalize(item['organization_type']))
                    item['organization_type'] = self.dir_org_config[type_type][item['organization_type']]
                else:  # we take the first value
                    item['organization_type'] = self.dir_org_config[type_type].values()[0]

            yield item


class ObjectUpdate(object):
    """ Check if we must do an object update """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.catalog = self.transmogrifier.context.portal_catalog
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.directory_path = self.storage['directory_path']
        self.ids = self.storage['ids']
        self.uniques = {}
        for typ in MANAGED_TYPES:
            pairs = options.get('{}_uniques'.format(typ), '').strip().split()
            if len(pairs) % 2:
                raise Exception("The '{}' section '{}' option must contain a even number of elements".format(name,
                                '{}_uniques'.format(typ)))
            self.uniques[typ] = [(f, i) for f, i in pairwise(pairs)]

    def __iter__(self):
        for item in self.previous:
            if '_path' in item:  # _path has already be set
                yield item
                continue
            item_type = item['_type']
            # we will do a search for each index
            for field, idx in self.uniques[item_type]:
                if item[field]:
                    brains = self.catalog.unrestrictedSearchResults({idx: item[field]})
                    if len(brains) > 1:
                        input_error(item, u"the search with '{}'='{}' get multiple objs: {}".format(idx, item[field],
                                          u', '.join([b.getPath() for b in brains])))
                    elif len(brains):
                        item['_path'] = relative_path(self.transmogrifier.context, brains[0].getPath())
                        item['_act'] = 'update'
                        # we store _path for each _id
                        self.ids[item_type][item['_id']]['path'] = item['_path']
                        break
                    else:
                        input_error(item, u"the search with '{}'='{}' get no result".format(idx, item[field]))
            yield item


class PathInserter(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.title_key = options.get('title-key', 'title')
        self.transmogrifier = transmogrifier
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.directory_path = self.storage['directory_path']
        self.ids = self.storage['ids']

    def __iter__(self):
        idnormalizer = getUtility(IIDNormalizer)
        for item in self.previous:
            if '_path' in item:  # _path has already be set
                yield item
                continue
            item_type = item['_type']
            title = item.get(self.title_key, None)
            if not title:
                continue
            new_id = idnormalizer.normalize(title)
            # put in directory by default
            item['_path'] = '/'.join([self.directory_path, new_id])
            # organization parent ?
            if item_type == 'organization' and item['_pid']:
                    item['_path'] = '/'.join([self.ids[item_type][item['_pid']]['path'], new_id])
            # we rename id if it already exists
            item['_path'] = correct_path(self.transmogrifier.context, item['_path'])
            item['_act'] = 'new'
            # we store _path for each _id
            self.ids[item_type][item['_id']]['path'] = item['_path']
            yield item

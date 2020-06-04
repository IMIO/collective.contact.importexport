# -*- coding: utf-8 -*-

from collective.contact.importexport import e_logger
from collective.contact.importexport.utils import get_main_path
from collective.contact.importexport.utils import input_error
from collective.contact.importexport.utils import valid_email
from collective.contact.importexport.utils import valid_phone
from collective.contact.importexport.utils import valid_zip
from collective.contact.importexport.utils import to_bool
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from Products.CMFPlone.utils import safe_unicode
from zope.annotation.interfaces import IAnnotations
from zope.interface import classProvides
from zope.interface import implements

import logging
import os

ANNOTATION_KEY = 'collective.contact.importexport'
MANAGED_TYPES = ['organization', 'person', 'held_position']


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
        self.storage['ids'] = {typ: {} for typ in MANAGED_TYPES}
#        self.storage['uniques'] = {typ: {} for typ in MANAGED_TYPES}
        self.storage['fieldnames'] = {typ: transmogrifier['config'].get('{}s_fieldnames'.format(typ), '').split()
                                      for typ in MANAGED_TYPES}
        self.storage['directory'] = transmogrifier.context.contacts

    def __iter__(self):
        for item in self.previous:
            yield item


class CommonInputChecks(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.fieldnames = self.storage['fieldnames']
        self.ids = self.storage['ids']
        self.uniques = self.storage.setdefault('uniques', {typ: {key: {} for key in
                                                                 options.get('{}_uniques'.format(typ), '').split()
                                                                 if key in self.fieldnames[typ]}
                                                           for typ in MANAGED_TYPES})
        self.booleans = {typ: {key: {} for key in options.get('{}_booleans'.format(typ), '').split()
                               if key in self.fieldnames[typ]}
                         for typ in MANAGED_TYPES}

    def __iter__(self):
        for item in self.previous:
            item_type = item['_type']

            # set correct values
            for fld in self.fieldnames[item_type]:
                item[fld] = safe_unicode(item[fld].strip(' '))

            # duplicated _id ?
            if not item['_id'] or item['_id'] in self.ids[item_type]:
                input_error(item, u"missing or duplicated id '{}', already present line {}".format(item['_id'],
                                  self.ids[item_type][item['_id']]['_ln']))
            self.ids[item_type][item['_id']] = item

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
            yield item

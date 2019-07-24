# -*- coding: utf-8 -*-

from collective.contact.importexport.utils import get_main_path
from collective.contact.importexport.utils import is_valid_zip
from collective.contact.importexport.utils import is_valid_phone
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from zope.annotation.interfaces import IAnnotations
from zope.interface import classProvides
from zope.interface import implements

import logging
import os

e_logger = logging.getLogger('ccie-transmo')
e_logger.setLevel(logging.INFO)


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

    def __iter__(self):
        for item in self.previous:
            yield item


class OrderOrganizations(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            yield item


class CheckOrgData(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.storage = IAnnotations(transmogrifier)
        self.previous = previous

    def __iter__(self):
        msg_output = "ORGA <%s> '%s' is not a valid %s"
        for item in self.previous:
            for field in self.storage['csv']['fields']:
                item[field] = item[field].strip()
            # on vérifie que le code postal est valide
            if not is_valid_zip(item['zip_code'], item['country']):
                msg_output = msg_output % (item['_oid'], item['zip_code'], 'zip code')
                e_logger.warning(msg_output)
                item['zip_code'] = ''
            # on vérifie le num tél
            if not is_valid_phone():
                msg_output = msg_output % (item['_oid'], item['phone'], 'phone number')
                e_logger.warning(msg_output)
                item['phone'] = ''

            yield item

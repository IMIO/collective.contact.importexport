# -*- coding: utf-8 -*-

from collections import OrderedDict
from collective.contact.importexport import e_logger
from collective.contact.importexport import logger
from collective.contact.importexport import o_logger
from collective.contact.importexport.config import ANNOTATION_KEY
from collective.contact.importexport.utils import alphanum
from collective.contact.importexport.utils import by4wise
from collective.contact.importexport.utils import get_country_code
from collective.contact.importexport.utils import log_error
from collective.contact.importexport.utils import send_report
from collective.contact.importexport.utils import shortcut
from collective.contact.importexport.utils import valid_date
from collective.contact.importexport.utils import valid_email
from collective.contact.importexport.utils import valid_phone
from collective.contact.importexport.utils import valid_value_in_list
from collective.contact.importexport.utils import valid_zip
from collective.contact.importexport.utils import to_bool
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from imio.helpers.transmogrifier import correct_path
from imio.helpers.transmogrifier import get_main_path
from imio.helpers.transmogrifier import relative_path
from imio.pyutils.system import dump_var
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

MANAGED_TYPES = ['organization', 'person', 'held_position']


class Initialization(object):
    """Initializes global variables to be used in next sections.

    Parameters:
        * basepath = O, absolute directory. If empty, buildout dir will be used.
        * subpath = O, if given, it will be appended to basepath.
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.workingpath = get_main_path(safe_unicode(options.get('basepath', '')),
                                         safe_unicode(options.get('subpath', '')))
        self.portal = transmogrifier.context
        efh = logging.FileHandler(os.path.join(self.workingpath, 'ie_input_errors.log'), mode='w')
        efh.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        efh.setLevel(logging.INFO)
        e_logger.addHandler(efh)
        ofh = logging.FileHandler(os.path.join(self.workingpath, 'ie_shortlog.log'), mode='w')
        ofh.setFormatter(logging.Formatter('%(message)s'))
        ofh.setLevel(logging.INFO)
        o_logger.addHandler(ofh)
        pipe_commit = transmogrifier.context.REQUEST.get('_pipeline_commit_', False)
        if pipe_commit:
            ecfh = logging.FileHandler(os.path.join(self.workingpath, 'ie_input_errors_commit.log'), mode='a')
            ecfh.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            ecfh.setLevel(logging.INFO)
            e_logger.addHandler(ecfh)
            ocfh = logging.FileHandler(os.path.join(self.workingpath, 'ie_shortlog_commit.log'), mode='a')
            ocfh.setFormatter(logging.Formatter('%(message)s'))
            ocfh.setLevel(logging.INFO)
            o_logger.addHandler(ocfh)

        # set working path in portal annotation to retrieve log files
        annot = IAnnotations(self.portal).setdefault(ANNOTATION_KEY, {})
        annot['wp'] = self.workingpath
        # set global variables in annotation
        self.storage = IAnnotations(transmogrifier).setdefault(ANNOTATION_KEY, {})
        self.storage['wp'] = self.workingpath
        self.storage['ids'] = {typ: {} for typ in MANAGED_TYPES}
        self.storage['csv_files'] = {typ: None for typ in MANAGED_TYPES}
        self.storage['fieldnames'] = {typ: transmogrifier['config'].get('{}s_fieldnames'.format(typ), '').split()
                                      for typ in MANAGED_TYPES}
        self.storage['set_lst'] = {}  # to store set and associated date
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
    """Checks input values.

    * check uniqueness of _id
    * check uniqueness of some fields
    * check zip code following pattern
    * check phone following country
    * check email format
    * manage organization type, enterprise_number, ...

    Parameters:
        * phone_country = O, phone country. Default: BE.
        * language = O, country language. Default: fr.
        * organization_uniques = O, organization fieldnames that must be uniques.
        * organization_booleans = O, organization fieldnames that must be converted to boolean.
        * organization_hyphen_newline = fieldnames where newline character is replaced by -
        * person_uniques = O, person fieldnames that must be uniques.
        * person_booleans = O, person fieldnames that must be converted to boolean.
        * held_position_uniques = O, held position fieldnames that must be uniques.
        * held_position_booleans = O, held position fieldnames that must be converted to boolean.
        * raise_on_error = O, raises exception if 1. Default 1. Can be set to 0.
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.fieldnames = self.storage['fieldnames']
        self.ids = self.storage['ids']
        self.csv_encoding = transmogrifier['config'].get('csv_encoding', 'utf8')
        self.phone_country = safe_unicode(options.get('phone_country', 'BE')).upper()
        self.languages = [safe_unicode(options.get('language', u'fr')).lower()]
        if 'en' not in self.languages:
            self.languages.append(u'en')
        self.uniques = {typ: {key: {} for key in safe_unicode(options.get('{}_uniques'.format(typ), '')).split()
                              if key in self.fieldnames[typ]}
                        for typ in MANAGED_TYPES}
        self.booleans = {typ: [key for key in safe_unicode(options.get('{}_booleans'.format(typ), '')).split()
                               if key in self.fieldnames[typ]]
                         for typ in MANAGED_TYPES}
        self.hyphens = {typ: [key for key in safe_unicode(options.get('{}_hyphen_newline'.format(typ), '')).split()
                              if key in self.fieldnames[typ]]
                        for typ in MANAGED_TYPES}
        self.storage['booleans'] = self.booleans
        self.dir_org_config = self.storage['dir_org_config']
        self.directory_path = self.storage['directory_path']
        self.roe = bool(int(options.get('raise_on_error', '1')))

    def __iter__(self):
        idnormalizer = getUtility(IIDNormalizer)
        for item in self.previous:
            item_type = item['_type']

            # set correct values
            for fld in self.fieldnames[item_type]:
                item[fld] = safe_unicode(item[fld].strip(' '), encoding=self.csv_encoding)
            for fld in self.hyphens.get(item_type, []):
                if '\n' in item[fld]:
                    item[fld] = ' - '.join([part.strip() for part in item[fld].split('\n') if part.strip()])

            if item_type == 'held_position':
                item['_fid'] = None  # we don't yet manage position

            # set directory as default parent
            item['_parent'] = self.directory_path

            # duplicated _id ?
            if not item['_id']:
                log_error(item, u"SKIPPING: missing id '_id'", level='critical')
                if self.roe:
                    raise Exception(u'Missing id ! See log...')
                continue
            if item['_id'] in self.ids[item_type][item['_set']]:
                log_error(item, u"SKIPPING: duplicated id '{}', already present line {}".format(item['_id'],
                          self.ids[item_type][item['_set']][item['_id']]['ln']), level='critical')
                if self.roe:
                    raise Exception(u'Duplicated id ! See log...')
            self.ids[item_type][item['_set']][item['_id']] = {'path': '', 'ln': item['_ln']}

            # uniqueness
            for key in self.uniques[item_type]:
                if not item[key]:
                    continue
                uniques = self.uniques[item_type][key].setdefault(item['_set'], {})
                if item[key] in uniques:
                    log_error(item, u"duplicated {} '{}', already present line {:d}".format(key, item[key],
                              uniques[item[key]]))
                else:
                    uniques[item[key]] = item['_ln']

            # to bool from int
            for key in self.booleans[item_type]:
                item[key] = to_bool(item, key)

            if 'country' in item:
                country_code = get_country_code(item, 'country', self.phone_country, self.languages)

            # check zip
            if 'zip_code' in item:
                item['zip_code'] = valid_zip(item, 'zip_code', country_code)

            # check phones
            for key in ('phone', 'cell_phone', 'fax'):
                if key in item:
                    item[key] = valid_phone(item, key, country_code, self.phone_country)

            # check email
            if 'email' in item:
                item['email'] = valid_email(item, 'email')

            # organization checks
            if item_type == 'organization':
                if item['_id'] == item['_oid']:
                    log_error(item, u'SKIPPING: _oid is equal to _id {}'.format(item['_id']), level='critical')
                    if self.roe:
                        raise Exception(u'Inconsistent _oid ! See log...')
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
                    log_error(item, u"SKIPPING: missing related person id", level='critical')
                    if self.roe:
                        raise Exception(u'Missing _pid ! See log...')
                    continue
                if not item['_oid'] and not item['_fid']:
                    log_error(item, u"SKIPPING: missing organization/position id", level='critical')
                    if self.roe:
                        raise Exception(u'Missing _oid/_fid ! See log...')
                    continue

            yield item


class RelationsInserter(object):
    """Add relations between held position and organization.

    Parameters:
        * raise_on_error = O, raises exception if 1. Default 1. Can be set to 0.
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.portal = transmogrifier.context
        self.catalog = self.portal.portal_catalog
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.ids = self.storage['ids']
        self.roe = bool(int(options.get('raise_on_error', '1')))

    def __iter__(self):
        intids = getUtility(IIntIds)
        for item in self.previous:
            item_type = item['_type']
            if item_type == 'held_position':
                if item['_oid'] and item['_oid'] not in self.ids['organization'][item['_set']]:
                    log_error(item, u"SKIPPING: invalid related organization id '{}'".format(item['_oid']),
                              level='critical')
                    if self.roe:
                        raise Exception(u'Cannot find _oid ! See log...')
                    continue
                # not using _pid yet
                org = self.portal.unrestrictedTraverse(self.ids['organization'][item['_set']][item['_oid']]['path'])
                item['position'] = RelationValue(intids.getId(org))
            yield item


class UpdatePathInserter(object):
    """Add _path if we have to do an element update.

    * searches existing objects following parameter, composed of quartet (field index item-condition must-exist)
    * if found, set _path and _act

    Arguments:
        * organization_uniques = M, quartets related to organizations
        * person_uniques = M, quartets related to persons
        * held_position_uniques = M, quartets related to held positions
        * raise_on_error = O, raises exception if 1. Default 1. Can be set to 0.
    """
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
        options['cbin'] = str(cbin)
        self.uniques = {}
        self.cbin_beh = {}
        for typ in MANAGED_TYPES:
            values = safe_unicode(options.get('{}_uniques'.format(typ), '')).strip().split()
            if len(values) % 4:
                raise Exception("The '{}' section '{}' option must contain a multiple of 4 elements".format(name,
                                '{}_uniques'.format(typ)))
            self.uniques[typ] = [(f, i, Condition(c, transmogrifier, name, options),
                                  Condition(e, transmogrifier, name, options)) for f, i, c, e in by4wise(values)]
            typ_fti = getattr(self.portal.portal_types, typ)
            self.cbin_beh[typ] = 'collective.behavior.internalnumber.behavior.IInternalNumberBehavior' in \
                                 typ_fti.behaviors
        self.roe = bool(int(options.get('raise_on_error', '1')))

    def __iter__(self):
        for item in self.previous:
            if '_path' in item:  # _path has already be set
                yield item
                continue
            item_type = item['_type']
            # we will do a search for each index
            for field, idx, condition, must_exist in self.uniques[item_type]:
                if item[field] and condition(item):
                    if field == 'internal_number' and idx == 'internal_number' and not self.cbin_beh[item_type]:
                        log_error(item, u"the internalnumber behavior is not defined on type {}".format(item_type),
                                  level='critical')
                        if self.roe:
                            raise Exception(u'The internalnumber behavior is not defined on type {}'.format(item_type))
                        continue
                    brains = self.catalog.unrestrictedSearchResults({'portal_type': item_type, idx: item[field]})
                    if len(brains) > 1:
                        log_error(item, u"the search with '{}'='{}' gets multiple objs: {}".format(
                            idx, item[field], u', '.join([b.getPath() for b in brains])), level='critical')
                        if self.roe:
                            raise Exception(u'Too more results ! See log...')
                        continue
                    elif len(brains):
                        item['_path'] = relative_path(self.portal, brains[0].getPath())
                        item['_act'] = 'update'
                        # we store _path for each _id
                        self.ids[item_type][item['_set']][item['_id']]['path'] = item['_path']
                        break
                    elif must_exist(item):
                        log_error(item, u"the search with '{}'='{}' doesn't get any result".format(idx, item[field]),
                                  level='critical')
                        if self.roe:
                            raise Exception(u'Must find something ! See log...')
            yield item


class ParentPathInserter(object):
    """Updates _parent following 'linked' elements in sub organization or held position.

    Parameters:
        * raise_on_error = O, raises exception if 1. Default 1. Can be set to 0.
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.portal = transmogrifier.context
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.fieldnames = self.storage['fieldnames']
        self.ids = self.storage['ids']
        self.roe = bool(int(options.get('raise_on_error', '1')))

    def __iter__(self):
        for item in self.previous:
            # organization parent ?
            item_type = item['_type']
            if item_type in ('organization', 'held_position') and item['_oid']:
                if item['_oid'] not in self.ids['organization'][item['_set']]:
                    log_error(item, u"SKIPPING: invalid parent organization id '{}'".format(item['_oid']),
                              level='critical')
                    if self.roe:
                        raise Exception(u'Cannot find parent ! See log...')
                    continue
                item['_parent'] = self.ids['organization'][item['_set']][item['_oid']]['path']
                item['_related_title'] = self.portal.unrestrictedTraverse(item['_parent']).get_full_title()
            # person parent ?
            if item_type == 'held_position':
                if item['_pid'] not in self.ids['person'][item['_set']]:
                    log_error(item, u"SKIPPING: invalid related person id '{}'".format(item['_pid']), level='critical')
                    if self.roe:
                        raise Exception(u'Cannot find related person ! See log...')
                    continue
                item['_parent'] = self.ids['person'][item['_set']][item['_pid']]['path']
            yield item


class MoveObject(object):
    """Moves existing object if necessary.

    Parameters:
        * raise_on_error = O, raises exception if 1. Default 1. Can be set to 0.
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.portal = transmogrifier.context
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.fieldnames = self.storage['fieldnames']
        self.ids = self.storage['ids']
        self.roe = bool(int(options.get('raise_on_error', '1')))

    def __iter__(self):
        for item in self.previous:
            if item['_type'] != 'directory' and item.get('_act', 'no') == 'update' and \
                    item['_parent'] != os.path.dirname(item['_path']):
                obj = self.portal.unrestrictedTraverse(item['_path'], default=None)
                if obj is None:
                    log_error(item, u"SKIPPING: cannot find existing object '{}'".format(item['_path']),
                              level='critical')
                    if self.roe:
                        raise Exception(u'Cannot find existing object ! See log...')
                    continue
                target = self.portal.unrestrictedTraverse(item['_parent'], default=None)
                if target is None:
                    log_error(item, u"SKIPPING: cannot find new parent '{}'".format(item['_parent']),
                              level='critical')
                    if self.roe:
                        raise Exception(u'Cannot find new parent ! See log...')
                    continue
                # we move the object and update path, so all the next sections will work on this path
                # constructor NO, update YES
                moved_obj = api.content.move(obj, target)
                # TODO manage organization_type see dir_org_config
                # print("'{}' moved to '{}'".format(item['_path'], item['_parent']))
                item['_path'] = relative_path(self.portal, '/'.join(moved_obj.getPhysicalPath()))
                self.ids[item['_type']][item['_set']][item['_id']]['path'] = item['_path']
                # indexes and relations are well updated
            yield item


class PathInserter(object):
    """Adds _path for new element.

    * Finds parent for sub organization and held position.
    * Defines id from parameter list (fields).

    Parameters:
        * organization_id_keys = M, organization normalized fieldnames.
        * person_id_keys = M, person normalized fieldnames.
        * held_position_id_keys = M, held position normalized fieldnames.
        * raise_on_error = O, raises exception if 1. Default 1. Can be set to 0.
    """
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
        self.roe = bool(int(options.get('raise_on_error', '1')))

    def __iter__(self):
        idnormalizer = getUtility(IIDNormalizer)
        for item in self.previous:
            if '_path' in item:  # _path has already be set
                yield item
                continue
            item_type = item['_type']
            title = u'-'.join([item[key] for key in self.id_keys[item_type] if item[key]])

            if item_type == 'held_position' and '_related_title' in item:
                title = u'-'.join([title, item.pop('_related_title')])

            if not title:
                log_error(item, u'cannot get an id from id keys {}'.format(self.id_keys[item_type]), level='critical')
                if self.roe:
                    raise Exception(u'No title ! See log...')
                continue
            new_id = idnormalizer.normalize(title)
            item['_path'] = '/'.join([item['_parent'], new_id])
            # we rename id if it already exists
            item['_path'] = correct_path(self.portal, item['_path'])
            item['_act'] = 'new'
            # we store _path for each _id
            self.ids[item_type][item['_set']][item['_id']]['path'] = item['_path']
            yield item


class TransitionsInserter(object):
    """Adds _transitions following _inactive column."""
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.portal = transmogrifier.context
        self.name = name
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.fieldnames = self.storage['fieldnames']
        for typ in MANAGED_TYPES:
            if '_inactive' in self.fieldnames[typ] and '_inactive' not in self.storage['booleans'][typ]:
                raise Exception("{}: _inactive field is not configured as boolean for type {} !".format(self.name, typ))

    def __iter__(self):
        for item in self.previous:
            if '_path' not in item:
                yield item
                continue
            if '_inactive' in item:
                obj = self.portal.unrestrictedTraverse(item['_path'], default=None)
                state = api.content.get_state(obj=obj)
                if item['_inactive'] and state == 'active':
                    item['_transitions'] = 'deactivate'
                elif not item['_inactive'] and state == 'deactivated':
                    log_error(item, u'_inactive is False and current state is deactivated: we do not activate')
            yield item


class LastSection(object):
    """Last section to do things at the end of each item process.

    * counts by type and action.
    * logs totals.
    * updates and dumps registry.

    Parameters:
        * send_mail = O, Send a mail with summary and errors. Default 0.
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.portal = transmogrifier.context
        self.sets = self.storage['set_lst']
        self.send_mail = bool(int(options.get('send_mail', '0')))

    def __iter__(self):
        for item in self.previous:
            sett = item['_set']
            if sett != 'all':
                self.sets[sett][shortcut(item['_type'])]['nb'] += 1
                self.sets[sett][shortcut(item['_type'])][shortcut(item['_act'])] += 1
                if '_error' in item:
                    self.sets[sett][shortcut(item['_type'])]['e'] += 1
            yield item

        # end of process
        registry = self.storage.get('registry_dic', {})
        to_send = [u'Summary of contact import:']
        errors = 0
        for sett in sorted(self.sets):
            msg = u"{}: {}".format(sett, u', '.join([u"'{}' => ({})".format(tp, u'nb={nb}, N={N}, U={U}, D={D}, '
                                                                                u'e={e}'.format(**self.sets[sett][tp]))
                                                     for tp in ('O', 'P', 'HP')
                                                     if self.sets[sett][tp]['nb']]))
            errors += sum([self.sets[sett][tp]['e'] for tp in ('O', 'P', 'HP')])
            o_logger.info(msg)
            to_send.append(msg)
            if self.sets[sett].pop('mode') == 'ssh':
                registry.update({sett: self.sets[sett]})
        # dump registry if CSVSshSourceSection section is used
        if 'registry_filename' in self.storage and self.transmogrifier.context.REQUEST.get('_pipeline_commit_', False):
            if registry:
                logger.info("Updating registry in '{}'".format(self.storage['registry_filename']))
                dump_var(self.storage['registry_filename'], registry)
        if errors:
            to_send.append(u'\nCheck log file because there are {} items in error !'.format(errors))
        if self.send_mail:
            send_report(self.portal, to_send)

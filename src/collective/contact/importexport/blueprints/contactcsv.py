# -*- coding: utf-8 -*-
from collective.contact.importexport import logger
from collective.contact.importexport.blueprints.main import ANNOTATION_KEY
from collective.contact.importexport.blueprints.main import MANAGED_TYPES
from collective.contact.importexport.utils import input_error
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from collective.transmogrifier.utils import Expression
from collective.transmogrifier.utils import openFileReference
from imio.pyutils.system import load_var
from imio.pyutils.system import runCommand
from Products.CMFPlone.utils import safe_unicode
from zope.annotation import IAnnotations
from zope.interface import classProvides
from zope.interface import implements

import csv
import os


class CSVDiskSourceSection(object):
    """ Open disk files from filenames ans store handlers """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        for typ in MANAGED_TYPES:
            filename = safe_unicode(options.get('{}s_filename'.format(typ), ''))
            if filename:
                file_ = openFileReference(transmogrifier, filename)
                if file_ is None:
                    raise Exception("Cannot open file '{}'".format(filename))
                self.storage['csv_files'][typ] = file_
        if self.storage['csv_files']['organization'] is None and self.storage['csv_files']['person'] is None:
            raise Exception('You must specify at least organizations or persons CSV')
        self.storage['set_lst'].update({0: {'dt': ''}})

    def __iter__(self):
        for item in self.previous:
            yield item
        yield {'set': 0}


class CSVSshSourceSection(object):
    """ Open disk files from filenames ans store handlers """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)

        # setup
        servername = safe_unicode(options.get('servername', ''))
        username = safe_unicode(options.get('username', ''))
        files_path = safe_unicode(options.get('server_files_path', ''))
        self.registry_filename = safe_unicode(options.get('registry_filename', ''))
        transfer_path = safe_unicode(options.get('transfer_path', '')) or u'/tmp'
        if not os.path.dirname(transfer_path):
            transfer_path = os.path.join(self.storage['wp'], transfer_path)
        if not servername or not username or not files_path or not self.registry_filename:
            logger.error('Missing server parameters or registry in csv_ssh_source section')
            raise Exception('Missing server parameters or registry in csv_ssh_source section')
        sshcmd = u'ssh {}@{} "{{}}"'.format(username, servername)
        scpcmd = u'scp {}@{}:{{}} {}'.format(username, servername, transfer_path)
        if not os.path.dirname(self.registry_filename):
            self.registry_filename = os.path.join(self.storage['wp'], self.registry_filename)
        self.storage['registry_filename'] = self.registry_filename
        self.registry = {}
        load_var(self.registry_filename, self.registry)
        self.storage['registry_dic'] = self.registry
        last_done = self.registry and max(self.registry) or ''

        # get files list
        (out, err, code) = runCommand(sshcmd.format(u'cd {}; ls'.format(files_path)))
        if code:
            logger.error("ERR:{}".format(''.join(err)))
            raise Exception('Cannot list server files')
        files = dict([(fil.strip('\n'), '') for fil in out])

        # take newer files
        to_do = []
        for dt in sorted([fil[:-4] for fil in files if fil.endswith('.txt')], reverse=True):
            if dt <= last_done:
                break
            to_do.insert(0, dt)

        # transfer files
        self.input_files = []
        for dt in to_do:
            rec = [dt, '', '', '']
            for i, typ in enumerate(MANAGED_TYPES, 1):
                filename = '{}_{}s.csv'.format(dt, typ)
                if filename in files:
                    cmd = scpcmd.format(os.path.join(files_path, filename))
                    (out, err, code) = runCommand(cmd)
                    if code:
                        logger.error("ERR:{}".format(''.join(err)))
                        raise Exception("Cannot run command '{}'".format(cmd))
                    rec[i] = os.path.join(transfer_path, filename)
            self.input_files.append(rec)

    def __iter__(self):
        for item in self.previous:
            yield item
        for j, rec in enumerate(self.input_files, 1):
            for i, typ in enumerate(MANAGED_TYPES, 1):
                filename = rec[i]
                if filename:
                    file_ = openFileReference(self.transmogrifier, filename)
                    if file_ is None:
                        raise Exception("Cannot open file '{}'".format(filename))
                    self.storage['csv_files'][typ] = file_
            if self.storage['csv_files']['organization'] is None and self.storage['csv_files']['person'] is None:
                raise Exception('You must specify at least organizations or persons CSV')
            self.storage['set_lst'].update({j: {'dt': rec[0]}})
            yield {'set': j}


class CSVReaderSection(object):
    """ Read as csv file handlers stored in self.storage['csv_files'][typ] """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)
        self.csv_headers = Condition(options.get('csv_headers', 'python:True'), transmogrifier, name, options)
        self.dialect = safe_unicode(options.get('dialect', 'excel'))
        self.fmtparam = dict(
            (key[len('fmtparam-'):],
             Expression(value, transmogrifier, name, options)(
                 options, key=key[len('fmtparam-'):])) for key, value
            in options.iteritems() if key.startswith('fmtparam-'))

    def __iter__(self):
        for item in self.previous:
            # we update 'set_lst' for lastsection
            self.storage['set_lst'][item['set']].update({tp: {'nb': 0, 'n': 0, 'U': 0} for tp in ('O', 'P', 'HP')})
            for typ in MANAGED_TYPES:
                if self.storage['csv_files'][typ] is None:
                    continue
                self.storage['ids'][typ][item['set']] = {}  # we add set identifier (to differentiate multiple files)
                for item2 in self.rows(typ, item['set']):
                    yield item2
            continue
            yield item

    def rows(self, typ, sett):
        logger.info(u"Reading set {:d} '{}' csv file ({})".format(sett, typ, self.storage['csv_files'][typ].name))
        reader = csv.DictReader(self.storage['csv_files'][typ], dialect=self.dialect,
                                fieldnames=self.storage['fieldnames'][typ], restkey='_rest',
                                restval='__NO_CO_LU_MN__', **self.fmtparam)
        for item in reader:
            item['_type'] = typ
            item['_set'] = sett
            item['_ln'] = reader.line_num
            # check fieldnames length on first line
            if reader.line_num == 1:
                reader.restval = u''
                if '_rest' in item:
                    input_error(item, u'STOPPING: some columns are not defined in fieldnames: {}'.format(item['_rest']))
                    break
                extra_cols = [key for (key, val) in item.items() if val == '__NO_CO_LU_MN__']
                if extra_cols:
                    input_error(item, u'STOPPING: to much columns defined in fieldnames: {}'.format(extra_cols))
                    break
                # pass headers if any
                if self.csv_headers:
                    continue
            yield item
        self.storage['csv_files'][typ].close()

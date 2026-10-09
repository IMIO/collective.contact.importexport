from collective.contact.importexport import e_logger
from collective.contact.importexport import o_logger
from collective.contact.importexport.testing import COLLECTIVE_CONTACT_IMPORTEXPORT_FUNCTIONAL_TESTING
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.transmogrifier import configuration_registry
from collective.transmogrifier.transmogrifier import Transmogrifier
from plone import api
from Products.CMFPlone.tests.utils import MockMailHost
from Products.MailHost.interfaces import IMailHost
from zope.component import getSiteManager
from zope.interface import implementer
from zope.interface import provider

import csv
import os
import re
import shutil
import tempfile
import unittest


COLLECTED = []

FIELDS = {
    'organization': 'organizations_fieldnames',
    'person': 'persons_fieldnames',
    'held_position': 'held_positions_fieldnames',
}
REGISTRY_PIPELINE = 'collective.contact.importexport.interfaces.IPipelineConfiguration.pipeline'


@provider(ISectionBlueprint)
@implementer(ISection)
class CollectorSection:
    """Test blueprint storing yielded items in COLLECTED."""

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            COLLECTED.append(dict(item))
            yield item


class PipelineTestCase(unittest.TestCase):
    """Builds csv files and runs (parts of) the default registry pipeline on them."""

    layer = COLLECTIVE_CONTACT_IMPORTEXPORT_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.directory = self.portal['mydirectory']
        self.tmpdir = tempfile.mkdtemp()
        self.counter = 0
        configuration_registry.clear()
        del COLLECTED[:]

    def tearDown(self):
        for logger_ in (e_logger, o_logger):
            for handler in list(logger_.handlers):
                handler.close()
                logger_.removeHandler(handler)
        configuration_registry.clear()
        shutil.rmtree(self.tmpdir)

    def setup_mailhost(self):
        """Replaces the portal mailhost by a mock one storing messages."""
        self.portal._original_MailHost = self.portal.MailHost
        self.portal.MailHost = mailhost = MockMailHost('MailHost')
        getSiteManager(context=self.portal).registerUtility(mailhost, provided=IMailHost)
        api.portal.set_registry_record('plone.email_from_address', 'site@example.com')
        return mailhost

    def write_csv(self, filename, fieldnames, rows):
        """Writes a csv with a header line. Rows are dicts, missing columns are left empty."""
        with open(os.path.join(self.tmpdir, filename), 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, restval='')
            writer.writerow({name: name for name in fieldnames})
            writer.writerows(rows)

    def prepare_pipeline(self, last_section='lastsection', sections=None, organizations=(), persons=(),
                         held_positions=(), replacements=None, files=None, filename=None):
        """Writes csv files and a pipeline file in the temporary directory.

        :param last_section: last section of the registry pipeline to keep (the `collector` one is added after)
        :param sections: explicit list of sections, replacing the registry ones
        :param organizations: organization rows (dicts)
        :param persons: person rows (dicts)
        :param held_positions: held position rows (dicts)
        :param replacements: dic of text replacements done in the pipeline
        :param files: dic of filename: raw text, written in place of the generated csv files
        :param filename: pipeline filename. Default pipelineN.cfg
        :return: pipeline file path
        """
        pipeline = api.portal.get_registry_record(REGISTRY_PIPELINE)
        lines = re.search(r'^pipeline =\n((?:[ \t]+\S+\n|#.*\n)+)', pipeline, re.M).group(1)
        if sections is None:
            sections = [line.strip() for line in lines.splitlines() if line.strip() and not line.startswith('#')]
            sections = sections[:sections.index(last_section) + 1]
        pipeline = pipeline.replace(lines, ''.join('    {}\n'.format(name) for name in sections + ['collector']))
        pipeline += '\n[collector]\nblueprint = collective.contact.importexport.tests.collector\n'
        replacements = {'basepath =': 'basepath = {}'.format(self.tmpdir), 'subpath = imports': 'subpath =',
                        'organizations-test.csv': 'organizations.csv', 'persons-test.csv': 'persons.csv',
                        'heldpositions-test.csv': 'held_positions.csv', 'send_mail = 1': 'send_mail = 0',
                        **(replacements or {})}
        for old, new in replacements.items():
            assert old in pipeline, old
            pipeline = pipeline.replace(old, new)
        for csv_filename, typ, rows in (('organizations.csv', 'organization', organizations),
                                        ('persons.csv', 'person', persons),
                                        ('held_positions.csv', 'held_position', held_positions)):
            fieldnames = re.search(r'^{} = (.*)$'.format(FIELDS[typ]), pipeline, re.M).group(1).split()
            self.write_csv(csv_filename, fieldnames, rows)
        for csv_filename, text in (files or {}).items():
            with open(os.path.join(self.tmpdir, csv_filename), 'w', encoding='utf-8', newline='') as csvfile:
                csvfile.write(text)
        self.counter += 1
        filepath = os.path.join(self.tmpdir, filename or 'pipeline{}.cfg'.format(self.counter))
        with open(filepath, 'w', encoding='utf-8') as pipeline_file:
            pipeline_file.write(pipeline)
        return filepath

    def run_pipeline(self, **kwargs):
        """Prepares (see prepare_pipeline) and runs a pipeline. Yielded items are returned (see COLLECTED)."""
        filepath = self.prepare_pipeline(**kwargs)
        del COLLECTED[:]
        pipeline_id = 'collective.contact.importexport.tests.pipeline{}'.format(self.counter)
        configuration_registry.registerConfiguration(pipeline_id, u'', u'', filepath)
        Transmogrifier(self.portal)(pipeline_id)
        return list(COLLECTED)

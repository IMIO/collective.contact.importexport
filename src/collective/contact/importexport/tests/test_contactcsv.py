from collective.contact.importexport.blueprints.contactcsv import open_csv
from collective.contact.importexport.tests.base import PipelineTestCase
from collective.transmogrifier.transmogrifier import configuration_registry
from collective.transmogrifier.transmogrifier import Transmogrifier
from imio.pyutils.system import load_var
from unittest import mock

import os
import shutil


class TestContactcsv(PipelineTestCase):

    def test_open_csv(self):
        transmogrifier = {'config': {'csv_encoding': 'latin-1'}}
        path = os.path.join(self.tmpdir, 'latin.csv')
        with open(path, 'w', encoding='latin-1', newline='') as latin_file:
            latin_file.write(u'é;à\r\n')
        with open_csv(transmogrifier, path) as csv_file:
            self.assertEqual(csv_file.read(), u'é;à\r\n')
        # default encoding is utf-8
        with open(path, 'w', encoding='utf-8', newline='') as utf_file:
            utf_file.write(u'é;à\r\n')
        with open_csv({'config': {'csv_encoding': ''}}, path) as csv_file:
            self.assertEqual(csv_file.read(), u'é;à\r\n')
        # package reference
        with open_csv({'config': {}}, 'collective.contact.importexport.tests:data/organizations.csv') as csv_file:
            self.assertIn(u'Rue Léon Morel', csv_file.read())
        self.assertIsNone(open_csv(transmogrifier, os.path.join(self.tmpdir, 'unknown.csv')))


class TestCSVDiskSourceSection(PipelineTestCase):

    def test_csv_disk_source(self):
        sections = ['initialization', 'csv_disk_source', 'csv_reader']
        organizations = [{'_id': '1', 'title': u'é', 'organization_type': u'Commune'}]
        # file encoding
        items = self.run_pipeline(sections=sections, organizations=organizations,
                                  replacements={'csv_encoding =': 'csv_encoding = latin-1'})
        self.assertEqual(items[0]['title'], u'é'.encode('utf-8').decode('latin-1'))
        # absolute file name
        shutil.move(os.path.join(self.tmpdir, 'organizations.csv'), os.path.join(self.tmpdir, 'absolute.csv'))
        items = self.run_pipeline(sections=sections, organizations=organizations, replacements={
            'organizations_filename = organizations.csv': 'organizations_filename = {}'.format(
                os.path.join(self.tmpdir, 'absolute.csv'))})
        self.assertEqual(items[0]['title'], u'é')
        # a latin-1 file read as utf-8 (Excel export)
        filepath = self.prepare_pipeline(
            last_section='common_input_checks', replacements={'csv_encoding =': 'csv_encoding = utf8'},
            organizations=[{'_id': '1', 'title': u'Liège', 'organization_type': u'Commune'}])
        with open(os.path.join(self.tmpdir, 'organizations.csv'), encoding='utf-8') as csv_file:
            text = csv_file.read()
        with open(os.path.join(self.tmpdir, 'organizations.csv'), 'w', encoding='latin-1') as csv_file:
            csv_file.write(text)
        configuration_registry.registerConfiguration('collective.contact.importexport.tests.latin', u'', u'', filepath)
        with self.assertRaises(UnicodeDecodeError):
            Transmogrifier(self.portal)('collective.contact.importexport.tests.latin')
        # missing file
        with self.assertRaisesRegex(Exception, "Cannot open file '{}".format(self.tmpdir)):
            self.run_pipeline(sections=sections, replacements={'persons.csv': 'unknown.csv'})
        # no file at all
        with self.assertRaisesRegex(Exception, 'You must specify at least organizations or persons CSV'):
            self.run_pipeline(sections=sections, replacements={'organizations_filename = organizations.csv': 'organizations_filename =',
                                                               'persons_filename = persons.csv': 'persons_filename ='})


class TestCSVSshSourceSection(PipelineTestCase):

    def setUp(self):
        super().setUp()
        self.sections = ['initialization', 'csv_ssh_source', 'csv_reader']
        self.transfer_dir = os.path.join(self.tmpdir, 'transfer')
        os.mkdir(self.transfer_dir)
        self.registry_path = os.path.join(self.tmpdir, '0_registry.dump')
        self.replacements = {
            'server_path = /srv/sftp/inbw/upload_success': 'server_path = /srv/sftp',
            'transfer_path =': 'transfer_path = {}'.format(self.transfer_dir),
            'registry_filename = 0_registry.dump': 'registry_filename = {}'.format(self.registry_path),
        }

    def fake_ssh(self, command):
        """Replaces the ssh/scp commands: distant files are generated in the local transfer directory."""
        if command.startswith('ssh'):
            return ['20991231-2359.txt\n', '20991231-2359_organizations.csv\n'], [], 0
        filename = command.split(':')[1].split()[0].split('/')[-1]
        shutil.copy(os.path.join(self.tmpdir, 'organizations.csv'), os.path.join(self.transfer_dir, filename))
        return [], [], 0

    def test_csv_ssh_source(self):
        # ssh and scp are external commands, they are replaced
        with mock.patch('collective.contact.importexport.blueprints.contactcsv.runCommand', side_effect=self.fake_ssh):
            organizations = [{'_id': '1', 'title': u'Commune', 'organization_type': u'Commune'}]
            items = self.run_pipeline(sections=self.sections, organizations=organizations,
                                      replacements=self.replacements)
        # the set is newer than the registry (empty)
        self.assertEqual([(item['_set'], item['_id']) for item in items], [('20991231-2359', '1')])
        # the option can also be named server_files_path
        with mock.patch('collective.contact.importexport.blueprints.contactcsv.runCommand', side_effect=self.fake_ssh):
            items = self.run_pipeline(sections=self.sections, organizations=organizations, replacements={
                **self.replacements, 'server_path = /srv/sftp': 'server_files_path = /srv/sftp'})
        self.assertEqual(len(items), 1)
        # missing parameters
        with self.assertRaisesRegex(Exception, 'Missing server parameters or registry in csv_ssh_source section'):
            self.run_pipeline(sections=self.sections, replacements={**self.replacements,
                                                                    'servername = sftp-client.imio.be': 'servername ='})
        # wrong transfer path
        with self.assertRaisesRegex(Exception, "scp transfert path .* doesn't exist"):
            self.run_pipeline(sections=self.sections, replacements={
                **self.replacements, 'transfer_path = {}'.format(self.transfer_dir): 'transfer_path = /unknown/path'})
        # ssh error
        with mock.patch('collective.contact.importexport.blueprints.contactcsv.runCommand',
                        return_value=([], ['error'], 1)):
            with self.assertRaisesRegex(Exception, 'Cannot list server files'):
                self.run_pipeline(sections=self.sections, replacements=self.replacements)
        # a committed import stores the set in the registry file: the next import skips it
        sections = ['initialization', 'csv_ssh_source', 'csv_reader', 'common_input_checks', 'dependencysorter',
                    'relationsinserter', 'updatepathinserter', 'parentpathinserter', 'moveobject', 'pathinserter',
                    'constructor', 'schemaupdater', 'reindexobject', 'short_log', 'lastsection']
        self.portal.REQUEST.set('_pipeline_commit_', True)
        with mock.patch('collective.contact.importexport.blueprints.contactcsv.runCommand', side_effect=self.fake_ssh):
            items = self.run_pipeline(sections=sections, organizations=organizations, replacements=self.replacements)
            self.assertEqual([(item['_set'], item['_act']) for item in items[1:]], [('20991231-2359', 'new')])
            registry = {}
            load_var(self.registry_path, registry)
            self.assertEqual(registry['20991231-2359']['O'], {'nb': 1, 'N': 1, 'U': 0, 'D': 0, 'e': 0})
            items = self.run_pipeline(sections=sections, organizations=organizations, replacements=self.replacements)
        self.assertEqual(items, [])


class TestCSVReaderSection(PipelineTestCase):

    def test_csv_reader(self):
        sections = ['initialization', 'csv_disk_source', 'csv_reader']
        organizations = [{'_id': '1', 'title': u'First'}, {'_id': '2', 'title': u'Second'}]
        persons = [{'_id': '1', 'lastname': u'Dupont'}]
        items = self.run_pipeline(sections=sections, organizations=organizations, persons=persons)
        # header lines are skipped
        self.assertEqual([(item['_type'], item['_id'], item['_ln']) for item in items],
                         [('organization', '1', 2), ('organization', '2', 3), ('person', '1', 2)])
        self.assertEqual(items[0]['title'], u'First')
        self.assertEqual(items[2]['lastname'], u'Dupont')
        # without header
        items = self.run_pipeline(sections=sections, organizations=organizations, persons=persons,
                                  replacements={'csv_headers = python:True': 'csv_headers = python:False'})
        self.assertEqual([item['_ln'] for item in items], [1, 2, 3, 1, 2, 1])
        # too many columns in file
        files = {'organizations.csv': u',' * 60 + u'\n'}
        with self.assertRaisesRegex(Exception, 'Some columns for organization are not defined in fieldnames'):
            self.run_pipeline(sections=sections, files=files)
        # not enough columns in file
        files = {'organizations.csv': u'_id,title\n1,A\n'}
        with self.assertRaisesRegex(Exception, 'To much columns for organization defined in fieldnames'):
            self.run_pipeline(sections=sections, files=files)
        # without exception
        no_raise = {'raise_on_error = 1': 'raise_on_error = 0'}
        items = self.run_pipeline(sections=sections, files=files, replacements=no_raise)
        self.assertEqual(items, [])
        self.assertIn('STOPPING: to much columns defined in fieldnames',
                      open(os.path.join(self.tmpdir, 'ie_input_errors.log')).read())

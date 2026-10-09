from collective.contact.importexport.interfaces import ICollectiveContactImportexportLayer
from collective.contact.importexport.tests.base import PipelineTestCase
from plone import api
from unittest import mock
from zope.interface import alsoProvides

import os


def read_log(directory, filename):
    with open(os.path.join(directory, filename), encoding='utf-8') as log_file:
        return log_file.read()


class TestExecutePipeline(PipelineTestCase):

    def test_call(self):
        # the view reads pipeline.cfg in the buildout directory, found from INSTANCE_HOME
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        files = {}
        for source, target in (('organizations', 'organizations'), ('persons', 'persons'),
                               ('heldpositions', 'held_positions')):
            with open(os.path.join(data_dir, source + '.csv'), encoding='utf-8') as data_file:
                files[target + '.csv'] = data_file.read()
        self.prepare_pipeline(files=files, filename='pipeline.cfg')
        request = self.layer['request']
        alsoProvides(request, ICollectiveContactImportexportLayer)
        view = api.content.get_view('execute-contact-pipeline', self.portal, request)
        with mock.patch.dict(os.environ, {'INSTANCE_HOME': os.path.join(self.tmpdir, 'parts', 'instance')}):
            self.assertIsNone(view())
        self.assertEqual(self.directory['imio'].title, u'IMIO')
        self.assertEqual(self.directory['test-company'].city, u'Liège')
        # the original phone numbers are not valid: they are logged, but items are not skipped
        self.assertNotIn('SKIPPING', read_log(self.tmpdir, 'ie_input_errors.log'))
        self.assertTrue(request.get('_pipeline_commit_'))
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'ie_shortlog_commit.log')))

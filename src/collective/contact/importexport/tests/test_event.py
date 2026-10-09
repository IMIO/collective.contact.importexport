from collective.contact.importexport.tests.base import PipelineTestCase
from collective.contact.importexport.tests.base import REGISTRY_PIPELINE
from plone import api
from unittest import mock

import os


class TestEvent(PipelineTestCase):

    def test_modified_pipeline(self):
        pipeline_path = os.path.join(self.tmpdir, 'pipeline.cfg')
        # the pipeline file is written in the buildout directory, found from INSTANCE_HOME
        with mock.patch.dict(os.environ, {'INSTANCE_HOME': os.path.join(self.tmpdir, 'parts', 'instance')}):
            api.portal.set_registry_record(REGISTRY_PIPELINE, u'[transmogrifier]\npipeline =\n    é\n')
            with open(pipeline_path, encoding='utf-8') as pipeline_file:
                self.assertEqual(pipeline_file.read(), u'[transmogrifier]\npipeline =\n    é\n')
            # same value: file is not written again
            os.remove(pipeline_path)
            api.portal.set_registry_record(REGISTRY_PIPELINE, u'[transmogrifier]\npipeline =\n    é\n')
            self.assertFalse(os.path.exists(pipeline_path))
            # another record: file is not written
            api.portal.set_registry_record(
                'collective.contact.importexport.interfaces.IPipelineConfiguration.emails', u'dest@example.com')
            self.assertFalse(os.path.exists(pipeline_path))

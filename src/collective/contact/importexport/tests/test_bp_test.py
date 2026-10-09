from collective.contact.importexport.tests.base import PipelineTestCase
from collective.transmogrifier.transmogrifier import configuration_registry
from collective.transmogrifier.transmogrifier import Transmogrifier
from collective.transmogrifier.utils import resolvePackageReferenceOrFile

import logging


class TestBpTest(PipelineTestCase):

    def test_bp_test(self):
        """The bp_test.cfg pipeline logs the call order of the sections generators."""
        filepath = resolvePackageReferenceOrFile('collective.contact.importexport.blueprints:bp_test.cfg')
        configuration_registry.registerConfiguration('collective.contact.importexport.bp_test', u'', u'', filepath)
        with self.assertLogs(logging.getLogger('transmo'), level='INFO') as logs:
            Transmogrifier(self.portal)('collective.contact.importexport.bp_test')
        # source2 doesn't yield the items of source1
        self.assertEqual(
            [line.split(':', 2)[2] for line in logs.output],
            ['source1 init', 'source2 init', 'constructor1 init', 'constructor2 init',
             'constructor2 before previous loop', 'constructor1 before previous loop', 'source2 before previous loop',
             'source1 before previous loop', 'source1 after previous loop']
            + ['source1 yield elem', 'source2 yield previous'] * 3
            + ['source1 after elem loop', 'source2 after previous loop']
            + ['source2 yield elem', 'constructor1 yield previous', 'constructor2 yield previous'] * 3
            + ['source2 after elem loop', 'constructor1 after previous loop', 'constructor2 after previous loop'])

from collective.contact.importexport.scripts.execute_pipeline import execute_pipeline
from collective.contact.importexport.tests.base import PipelineTestCase
from collective.transmogrifier.transmogrifier import configuration_registry
from email import message_from_string
from email.header import decode_header
from email.header import make_header
from plone import api


class TestExecutePipeline(PipelineTestCase):

    def test_execute_pipeline(self):
        organizations = [{'_id': '1', 'title': u'Commune', 'organization_type': u'Commune'}]
        filepath = self.prepare_pipeline(organizations=organizations)
        execute_pipeline(self.portal, filepath)
        self.assertEqual(self.directory['commune'].title, u'Commune')
        # configuration is registered once
        execute_pipeline(self.portal, filepath)
        self.assertEqual(self.directory['commune-1'].title, u'Commune')

        # a missing csv file stops the pipeline: an email reports the error
        configuration_registry.clear()
        mailhost = self.setup_mailhost()
        api.portal.set_registry_record(
            'collective.contact.importexport.interfaces.IPipelineConfiguration.emails', u'dest@example.com')
        filepath = self.prepare_pipeline(replacements={'organizations.csv': 'unknown.csv'}, organizations=[])
        with self.assertRaisesRegex(Exception, 'Cannot open file'):
            execute_pipeline(self.portal, filepath)
        self.assertEqual(len(mailhost.messages), 1)
        message = message_from_string(mailhost.messages[0].decode())
        self.assertEqual(str(make_header(decode_header(message['Subject']))), 'Contact import report')
        text = message.get_payload()[0].get_payload()[1].get_payload(decode=True).decode()
        self.assertIn('Critical error during pipeline', text)

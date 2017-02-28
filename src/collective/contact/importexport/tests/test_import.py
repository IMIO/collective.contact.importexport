# -*- coding: utf-8 -*-
from collective.contact.importexport.browser.import_view import are_headers_in_fields  # noqa
from collective.contact.importexport.testing import COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING  # noqa
from io import BytesIO
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from ZPublisher.HTTPRequest import ZopeFieldStorage, FileUpload
import unittest
import os


class TestImport(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.directory = api.content.create(
            container=self.portal,
            type='directory',
            id='mydirectory'
        )

    def test_empty_or_no_files(self):
        view_name = 'collective_contact_importexport_import_view'
        form = self.directory.restrictedTraverse(view_name)
        form.update()
        self.assertIsNone(form.handleApply(form, {}))

    def _create_test_file_field(self, file_name='organizations.csv'):
        field_storage = ZopeFieldStorage()
        data_path = os.path.join(os.path.dirname(__file__), 'data')
        file_path = os.path.join(data_path, file_name)
        data = open(file_path, 'r').read()
        field_storage.file = BytesIO(data)
        field_storage.filename = file_name
        file_field = FileUpload(field_storage)
        return file_field

    def test_files_bad_formatted(self):
        pass

    def test_import_orga(self):
        view_name = 'collective_contact_importexport_import_view'
        form = self.directory.restrictedTraverse(view_name)
        form.update()
        ofile = self._create_test_file_field('organizations.csv')
        form.request.form['form.widgets.organizations_file'] = ofile
        form.request.form['form.widgets.state'] = 'active'
        self.assertEqual(len(self.directory.contentValues()), 0)
        form.handleApply(form, form.request.form)
        self.assertEqual(len(self.directory.contentValues()), 1)

    def test_are_headers_in_fields(self):
        headers = ['id', 'field1', 'field2']
        fields = ['field1', 'field2']
        poral_type = 'organizations'
        self.assertTrue(are_headers_in_fields(headers, fields, poral_type))
        fields = ['field1', 'field2', 'fields3']
        headers = ['id', 'field1', 'field2', 'fields4']
        self.assertFalse(are_headers_in_fields(headers, fields, poral_type))

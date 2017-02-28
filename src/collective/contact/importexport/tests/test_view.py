# -*- coding: utf-8 -*-
from collective.contact.importexport.testing import COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING  # noqa
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


class TestView(unittest.TestCase):
    """ """

    layer = COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.directory = api.content.create(
            container=self.portal,
            type='directory',
            id='mydirectory'
        )

    def test_import_tab(self):
        view = api.content.get_view(
            name='view',
            context=self.directory,
            request=self.portal.REQUEST
        )
        page = view()
        self.assertTrue('collective_contact_importexport_import_view' in page)

    def test_form(self):
        view_name = 'collective_contact_importexport_import_view'
        form = self.directory.restrictedTraverse(view_name)
        self.assertTrue('organizations_file' in form())

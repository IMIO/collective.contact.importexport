# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from collective.contact.importexport.testing import COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING  # noqa
from plone import api

import unittest


class TestSetup(unittest.TestCase):
    """Test that collective.contact.importexport is properly installed."""

    layer = COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if collective.contact.importexport is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'collective.contact.importexport'))

    def test_registry(self):
        """Test if registry record is defined."""
        value = api.portal.get_registry_record('collective.contact.importexport.interfaces.IPipelineConfiguration.'
                                               'pipeline')
        self.assertIn(u'transmogrifier', value)

    def test_browserlayer(self):
        """Test that ICollectiveContactImportexportLayer is registered."""
        from collective.contact.importexport.interfaces import (
            ICollectiveContactImportexportLayer)
        from plone.browserlayer import utils
        self.assertIn(
            ICollectiveContactImportexportLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        self.installer.uninstallProducts(['collective.contact.importexport'])

    def test_product_uninstalled(self):
        """Test if collective.contact.importexport is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'collective.contact.importexport'))

    def test_browserlayer_removed(self):
        """Test that ICollectiveContactImportexportLayer is removed."""
        from collective.contact.importexport.interfaces import \
            ICollectiveContactImportexportLayer
        from plone.browserlayer import utils
        self.assertNotIn(
           ICollectiveContactImportexportLayer,
           utils.registered_layers())

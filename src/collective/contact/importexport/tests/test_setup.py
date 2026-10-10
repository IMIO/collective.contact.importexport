"""Setup tests for this package."""

from collective.contact.importexport.interfaces import ICollectiveContactImportexportLayer
from collective.contact.importexport.testing import COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING  # noqa
from plone import api
from plone.base.utils import get_installer
from plone.browserlayer import utils

import unittest


class TestSetup(unittest.TestCase):
    """Test that collective.contact.importexport is properly installed."""

    layer = COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.installer = get_installer(self.portal)

    def test_product_installed(self):
        """Test if collective.contact.importexport is installed."""
        self.assertTrue(self.installer.is_product_installed("collective.contact.importexport"))

    def test_registry(self):
        """Test if registry record is defined."""
        value = api.portal.get_registry_record(
            "collective.contact.importexport.interfaces.IPipelineConfiguration." "pipeline"
        )
        self.assertIn("transmogrifier", value)

    def test_directory_import_action(self):
        """No Import action on directories (its view was removed in 1.0.0)."""
        self.assertIsNone(self.portal.portal_types.directory.getActionObject("object/collective_contact_import"))

    def test_browserlayer(self):
        """Test that ICollectiveContactImportexportLayer is registered."""
        self.assertIn(ICollectiveContactImportexportLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.installer = get_installer(self.portal)
        self.installer.uninstall_product("collective.contact.importexport")

    def test_product_uninstalled(self):
        """Test if collective.contact.importexport is cleanly uninstalled."""
        self.assertFalse(self.installer.is_product_installed("collective.contact.importexport"))

    def test_browserlayer_removed(self):
        """Test that ICollectiveContactImportexportLayer is removed."""
        self.assertNotIn(ICollectiveContactImportexportLayer, utils.registered_layers())

from collective.contact.importexport.setuphandlers import HiddenProfiles
from collective.contact.importexport.setuphandlers import post_install
from collective.contact.importexport.setuphandlers import uninstall
from collective.contact.importexport.testing import COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING
from collective.contact.importexport.tests.base import REGISTRY_PIPELINE
from plone import api
from plone.base.interfaces import INonInstallable
from zope.component import getAllUtilitiesRegisteredFor

import unittest


class TestHiddenProfiles(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING

    def test_getNonInstallableProfiles(self):
        self.assertEqual(HiddenProfiles().getNonInstallableProfiles(), ["collective.contact.importexport:uninstall"])
        hidden = [
            profile
            for util in getAllUtilitiesRegisteredFor(INonInstallable)
            for profile in util.getNonInstallableProfiles()
        ]
        self.assertIn("collective.contact.importexport:uninstall", hidden)


class TestSetuphandlers(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING

    def test_post_install(self):
        default = api.portal.get_registry_record(REGISTRY_PIPELINE)
        self.assertIn("[transmogrifier]", default)
        # a configured pipeline is kept
        api.portal.set_registry_record(REGISTRY_PIPELINE, "my pipeline")
        post_install(None)
        self.assertEqual(api.portal.get_registry_record(REGISTRY_PIPELINE), "my pipeline")
        # an empty pipeline is replaced by the default one
        api.portal.set_registry_record(REGISTRY_PIPELINE, "")
        post_install(None)
        self.assertEqual(api.portal.get_registry_record(REGISTRY_PIPELINE), default)

    def test_uninstall(self):
        self.assertIsNone(uninstall(None))

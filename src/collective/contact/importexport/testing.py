# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import collective.contact.importexport


class CollectiveContactImportexportLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(
            name='testing.zcml',
            package=collective.contact.importexport)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'collective.contact.importexport:default')


COLLECTIVE_CONTACT_IMPORTEXPORT_FIXTURE = CollectiveContactImportexportLayer()


COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_CONTACT_IMPORTEXPORT_FIXTURE,),

    name='CollectiveContactImportexportLayer:IntegrationTesting'
)


COLLECTIVE_CONTACT_IMPORTEXPORT_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_CONTACT_IMPORTEXPORT_FIXTURE,),
    name='CollectiveContactImportexportLayer:FunctionalTesting'
)


COLLECTIVE_CONTACT_IMPORTEXPORT_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        COLLECTIVE_CONTACT_IMPORTEXPORT_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE
    ),
    name='CollectiveContactImportexportLayer:AcceptanceTesting'
)

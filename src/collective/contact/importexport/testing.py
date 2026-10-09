from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.testing import zope
from zope.globalrequest import setLocal

import collective.contact.core
import collective.contact.importexport
import transaction


class CollectiveContactImportexportLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(name='testing.zcml', package=collective.contact.core)
        self.loadZCML(name='testing.zcml', package=collective.contact.importexport)

    def setUpPloneSite(self, portal):
        setLocal('request', portal.REQUEST)  # for fingerpointing
        setRoles(portal, TEST_USER_ID, ['Manager'])
        applyProfile(portal, 'collective.contact.core:testing')
        applyProfile(portal, 'collective.contact.core:test_data')  # creates a directory
        applyProfile(portal, 'collective.contact.importexport:default')
        transaction.commit()


COLLECTIVE_CONTACT_IMPORTEXPORT_FIXTURE = CollectiveContactImportexportLayer()


COLLECTIVE_CONTACT_IMPORTEXPORT_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_CONTACT_IMPORTEXPORT_FIXTURE,),
    name='CollectiveContactImportexportLayer:IntegrationTesting'
)


COLLECTIVE_CONTACT_IMPORTEXPORT_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_CONTACT_IMPORTEXPORT_FIXTURE,),
    name='CollectiveContactImportexportLayer:FunctionalTesting'
)


ACCEPTANCE = FunctionalTesting(
    bases=(COLLECTIVE_CONTACT_IMPORTEXPORT_FIXTURE, REMOTE_LIBRARY_BUNDLE_FIXTURE, zope.WSGI_SERVER_FIXTURE),
    name='CollectiveContactImportexportLayer:AcceptanceTesting'
)

from collective.contact.importexport.scripts.execute_pipeline import execute_pipeline
from imio.helpers.transmogrifier import get_main_path
from plone.protect.interfaces import IDisableCSRFProtection
from Products.Five import BrowserView
from zope.interface import alsoProvides

import os


class ExecutePipeline(BrowserView):
    """View calling transmogrifier on pipeline.
    It can be called by Products.cron4plone by example."""

    def __call__(self):
        # called by cron/curl with an authenticated GET (no CSRF token): plone.protect would abort the import
        alsoProvides(self.request, IDisableCSRFProtection)
        portal = self.context
        portal.REQUEST.set("_pipeline_commit_", True)
        pipeline_path = os.path.join(get_main_path(), "pipeline.cfg")
        execute_pipeline(portal, pipeline_path)

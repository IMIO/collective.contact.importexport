# -*- coding: utf-8 -*-

from collective.contact.importexport.scripts.execute_pipeline import execute_pipeline
from imio.helpers.transmogrifier import get_main_path
from Products.Five import BrowserView

import os


class ExecutePipeline(BrowserView):
    """View calling transmogrifier on pipeline.
    It can be called by Products.cron4plone by example."""

    def __call__(self):
        portal = self.context
        portal.REQUEST.set('_pipeline_commit_', True)
        pipeline_path = os.path.join(get_main_path(), 'pipeline.cfg')
        execute_pipeline(portal, pipeline_path)

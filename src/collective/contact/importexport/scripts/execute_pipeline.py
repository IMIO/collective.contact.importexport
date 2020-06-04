# -*- coding: utf-8 -*-

from collective.transmogrifier.transmogrifier import configuration_registry
from collective.transmogrifier.transmogrifier import Transmogrifier
from zope.component.hooks import setSite

import sys
import transaction


PIPELINE_ID = 'collective.contact.importexport.pipeline'
USAGE = """
Usage : bin/instance run \
src/collective/contact/importexport/scripts/execute_pipeline.py \
PILELINE_FILE PLONE_ID
"""


def execute_pipeline(portal, filepath):
    try:
        configuration_registry.getConfiguration(PIPELINE_ID)
    except KeyError:
        configuration_registry.registerConfiguration(PIPELINE_ID, u'', u'', filepath)
    transmogrifier = Transmogrifier(portal)
    transmogrifier(PIPELINE_ID)


if 'app' in locals():
    # Called from bin/instance run
    args = sys.argv
    if len(args) < 5:
        print USAGE
        sys.exit(0)
    pipeline_filepath = sys.argv[3]
    plone_id = sys.argv[4]
    app = locals().get('app')
    portal = app.get(plone_id)
    setSite(portal)
    execute_pipeline(portal, pipeline_filepath)
    transaction.commit()

# -*- coding: utf-8 -*-

from AccessControl.SecurityManagement import newSecurityManager
from collective.contact.importexport import logger
from collective.contact.importexport.utils import send_report
from collective.transmogrifier.transmogrifier import configuration_registry
from collective.transmogrifier.transmogrifier import Transmogrifier
from imio.helpers.security import setup_logger
from Testing import makerequest
from zope.component.hooks import setSite
from zope.globalrequest import setRequest

import sys
import transaction


PIPELINE_ID = 'collective.contact.importexport.pipeline'
USAGE = """
Usage : bin/instance run \
src/collective/contact/importexport/scripts/execute_pipeline.py \
PILELINE_FILE PLONE_ID COMMIT_0_1
"""


def execute_pipeline(portal, filepath):
    try:
        configuration_registry.getConfiguration(PIPELINE_ID)
    except KeyError:
        configuration_registry.registerConfiguration(PIPELINE_ID, u'', u'', filepath)
    try:
        transmogrifier = Transmogrifier(portal)
        transmogrifier(PIPELINE_ID)
    except Exception as error:
        to_send = [u'Critical error during pipeline: {}'.format(error)]
        send_report(portal, to_send)
        raise error


if 'app' in locals():
    # Called from bin/instance run
    args = sys.argv
    if len(args) < 6 or sys.argv[5] not in ('0', '1'):
        print USAGE
        sys.exit(0)
    pipeline_filepath = sys.argv[3]
    plone_id = sys.argv[4]
    commit = bool(int(sys.argv[5]))
    app = locals().get('app')
    # plone_id can be 'folder/plone'
    root = app
    for pid in plone_id.split('/'):
        portal = root.get(pid)
        root = portal
    setSite(portal)
    acl_users = app.acl_users
    user = acl_users.getUser('admin')
    if user:
        user = user.__of__(acl_users)
        newSecurityManager(None, user)
    else:
        logger.error("Cannot find admin user ")
    app = makerequest.makerequest(app)
    # support plone.subrequest
    app.REQUEST['PARENTS'] = [app]
    setRequest(app.REQUEST)
    # can be used to increase temporary run verbosity
    # setup_logger(20)

    portal.REQUEST.set('_pipeline_commit_', commit)
    execute_pipeline(portal, pipeline_filepath)
    if commit:
        transaction.commit()

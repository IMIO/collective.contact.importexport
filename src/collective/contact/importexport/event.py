# -*- coding: utf-8 -*-
from imio.helpers.content import safe_encode
from imio.helpers.transmogrifier import get_main_path
from plone.registry.interfaces import IRecordModifiedEvent

import logging
import os

logger = logging.getLogger('collective.contact.importexport')


def modified_pipeline(obj, event):
    if event.record.__name__ != 'collective.contact.importexport.interfaces.IPipelineConfiguration.pipeline':
        return
    if IRecordModifiedEvent.providedBy(event) and event.oldValue == event.newValue:
        return
    if not hasattr(event, 'newValue'):
        new_val = event.record.value
    else:
        new_val = event.newValue
    if new_val is None:
        return
    new_val = safe_encode(new_val)
    path = get_main_path()
    pipeline_path = os.path.join(path, 'pipeline.cfg')
    fd = open(pipeline_path, 'w')
    fd.writelines(new_val)
    fd.close()
    logger.info('Pipeline was placed in {}'.format(pipeline_path))

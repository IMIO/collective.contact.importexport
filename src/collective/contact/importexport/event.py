# -*- coding: utf-8 -*-

from plone.registry.interfaces import IRecordModifiedEvent
from collective.contact.importexport.utils import get_main_path

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
    path = get_main_path()
    pipeline_path = os.path.join(path, 'pipeline.cfg')
    fd = open(pipeline_path, 'w')
    fd.writelines(new_val)
    fd.close()
    logger.info('Pipeline was placed in {}'.format(pipeline_path))

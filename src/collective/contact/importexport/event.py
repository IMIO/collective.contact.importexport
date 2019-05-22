# -*- coding: utf-8 -*-

import logging
import os

logger = logging.getLogger('collective.contact.importexport')


def modified_pipeline(obj, event):
    if event.oldValue == event.newValue:
        return
    CLIENT_HOME = os.environ['CLIENT_HOME']
    pipeline_path = os.path.join(CLIENT_HOME, 'pipeline.cfg')
    fd = open(pipeline_path, "w")
    fd.writelines(event.newValue)
    fd.close()
    logger.info("New pipeline.cfg file was placed in var/instance")

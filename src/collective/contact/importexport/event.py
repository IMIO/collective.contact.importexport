# -*- coding: utf-8 -*-

from collective.contact.importexport.utils import get_main_path

import logging
import os

logger = logging.getLogger('collective.contact.importexport')


def modified_pipeline(obj, event):
    if event.oldValue == event.newValue:
        return
    path = get_main_path()
    pipeline_path = os.path.join(path, 'pipeline.cfg')
    fd = open(pipeline_path, "w")
    fd.writelines(event.newValue)
    fd.close()
    logger.info("Pipeline was placed in {}".format(pipeline_path))

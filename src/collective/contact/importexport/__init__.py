# -*- coding: utf-8 -*-
"""Init and utils."""
from zope.i18nmessageid import MessageFactory
import logging

logger = logging.getLogger('ccie')
logger.setLevel(logging.INFO)  # neede to be displayed with instance run

e_logger = logging.getLogger('ccie-input')
e_logger.setLevel(logging.INFO)

_ = MessageFactory('collective.contact.importexport')

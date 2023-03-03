# -*- coding: utf-8 -*-
"""Init and utils."""
from zope.i18nmessageid import MessageFactory
import logging

# type shortcuts and action shortcuts
T_S = {u'organization': u'O', u'person': u'P', u'held_position': u'HP'}
A_S = {'new': u'N', 'update': u'U', 'delete': u'D'}

logger = logging.getLogger('ccie')
logger.setLevel(logging.INFO)  # needed to be displayed with instance run

e_logger = logging.getLogger('ccie-input')
e_logger.setLevel(logging.INFO)

o_logger = logging.getLogger('ccie-output')
o_logger.setLevel(logging.INFO)

_ = MessageFactory('collective.contact.importexport')

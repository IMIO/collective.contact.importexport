# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from collective.contact.importexport import _
from plone.supermodel import model
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope import schema


class ICollectiveContactImportexportLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IPipelineConfiguration(model.Schema):
    """Schema for registry record."""

    pipeline = schema.Text(
        title=_("Pipeline to import contacts"),
        description=_(u'Will be saved on disk as pipeline.cfg'),
    )

    emails = schema.TextLine(
        title=_("Emails list where to send report"),
        description=_(u'Values separated by comma. If empty, no report will be send'),
        required=False,
    )

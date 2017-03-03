# -*- coding: utf-8 -*-
from collective.contact.importexport import _
from plone import api
from plone.app.textfield.value import RichTextValue
from plone.dexterity.interfaces import IDexterityFTI
from plone.directives import form
from plone.namedfile.field import NamedFile
from plone.supermodel.interfaces import FIELDSETS_KEY
from plone.supermodel.utils import mergedTaggedValueList
from Products.CMFPlone.utils import safe_unicode
from z3c.form import button
from zope import schema
from zope.component import getUtility
from zope.component.interface import nameToInterface
from zope.schema import getFieldsInOrder

import csv
import logging
import StringIO


logger = logging.getLogger('collective.context.importexport import')


# fields = (
#     u'title',
#     u'description',
#     u'activity',
#     # u'subtitle',
#     u'street',
#     u'number',
#     u'additional_address_details'
#     u'zip_code',
#     u'city',
#     u'phone',
#     u'cell_phone',
#     u'fax',
#     u'email',
#     u'website',
#     u'region',
#     u'country',
# )

help_text = _(u"""
<p>
You can import organization from a csv file. This file should contains headers:
If you have a flat list of organizations, let id and id_parent fields empty.
<ul>
    <li>id</li>
    <li>id_parent</li>
    <li>title</li>
    <li>description</li>
    <li>activity</li>
    <li>street</li>
    <li>number</li>
    <li>additional_address_details</li>
    <li>zip_code</li>
    <li>city</li>
    <li>phone</li>
    <li>cell_phone</li>
    <li>fax</li>
    <li>email</li>
    <li>website</li>
    <li>region</li>
    <li>country</li>
</ul>
Other column will be added into activity field.
If a header match with a organization field, it will be added in field.
</p>
""")


class IImportForm(form.Schema):
    """ Define form fields """

    state = schema.Choice(
        title=_(u'State after creation'),
        description=_(u'Please select state for objects created.'),
        required=True,
        default='active',
        vocabulary=u'plone.app.vocabularies.WorkflowStates'
    )

    organizations_file = NamedFile(
        title=_(u"Organizations file"),
        description=_(u'Import csv organizations file'),
        required=False
    )
    # persons_file = NamedFile(
    #     title=_(u"Persons file"),
    #     description=_(u'Import xls persons file'),
    #     required=False
    # )
    # functions_file = NamedFile(
    #     title=_(u"Functions file"),
    #     description=_(u'Import xls functions file'),
    #     required=False
    # )
    # occupied_functions_file = NamedFile(
    #     title=_(u"Occupied functions file"),
    #     description=_(u'Import xls occupied functions file'),
    #     required=False
    # )


class ImportForm(form.SchemaForm):
    """ Define Form handling """
    name = _(u"Import contacts")
    schema = IImportForm
    ignoreContext = True

    label = u"Import contacts from CSV files"

    description = help_text

    def process_csv(self, data, portal_type):
        """
        """
        # sort and order organizations
        io = StringIO.StringIO(data)
        reader = csv.reader(io, delimiter=';', dialect='excel', quotechar='"')
        headers = reader.next()
        tot = len(headers)
        data = list(reader)
        row_count = len(data)

        def get_cell(row, name):
            """ Read one cell on a
            @param row: CSV row as list
            @param name: Column name: 1st row cell content value, header
            """
            assert type(name) == unicode, 'Column names must be unicode'
            index = None
            for i in range(0, tot):
                if headers[i].decode('utf-8') == name:
                    index = i
            if index is None:
                # raise RuntimeError('CSV data does not have column:' + name)
                logger.info('CSV data does not have column:' + name)
                return u''
            else:
                return row[index].decode('utf-8')

        fields = get_all_fields_from(portal_type)

        are_headers_in_fields(headers, fields, portal_type)
        updated = 0
        for row in data:
            contents = {}
            activity = ['<p>']
            for head in headers:
                if head in fields:
                    contents[head] = get_cell(
                        row,
                        safe_unicode(head)
                    )
                else:
                    activity.append(get_cell(
                        row,
                        safe_unicode(head)
                    ))
            # do not get empty lines/title of csv
            if contents.get('title', False):
                from plone.i18n.normalizer.interfaces import IURLNormalizer
                futur_name = getUtility(
                    IURLNormalizer).normalize(contents['title'])
                if futur_name not in self.context.contentIds():
                    obj = api.content.create(
                        container=self.context,
                        type=portal_type,
                        title=contents['title']
                    )
                    for key, value in contents.items():
                        if key == 'activity':
                            activity.append(value)
                        setattr(obj, key, value)
                    activity.append(u'</p>')
                    obj.activity = RichTextValue(u'<br />'.join(activity))

                    updated += 1
                    api.content.transition(obj=obj, to_state=self.next_state)
                    obj.reindexObject()
                    logger.info('{0}/{1}: {2} added'.format(
                        updated,
                        row_count,
                        obj.title.encode('utf8'))
                    )
                else:
                    logger.info('{0} already exists'.format(
                        contents['title'].encode('utf8'))
                    )
        return updated

    @button.buttonAndHandler(_(u'Import'), name='import')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.next_state = data.get('state')

        if data.get('organizations_file'):
            organizations_file = data['organizations_file'].data
            number = self.process_csv(organizations_file, 'organization')
            if number is not None:
                self.status = 'File uploaded. {0} new organizations created.'.format(number)  # noqa

        # if data.get('persons_file'):
        #     persons_file = data['persons_file'].data
        #     number = self.process_csv(persons_file)
        #     if number is not None:
        #         self.status = "File uploaded. {} new persons created.".format(number)  # noqa

        #
        # if data.get('functions_file'):
        #     functions_file = data['functions_file'].data
        #     number = self.process_csv(functions_file)
        #     if number is not None:
        #         self.status = "File uploaded. {} new functions created.".format(number)  # noqa

        #
        # if data.get('occupied_functions_file'):
        #     occupied_functions_file = data['occupied_functions_file'].data
        #     number = self.process_csv(occupied_functions_file)
        #     if number is not None:
        #         self.status = "File uploaded. {} new occupied functions created.".format(number)  # noqa


def get_all_fields_from(portal_type):
    portal_types = api.portal.get_tool('portal_types')
    portal = api.portal.get()
    schema = getUtility(IDexterityFTI, name=portal_type).lookupSchema()
    fields = []
    for name, field in getFieldsInOrder(schema):
        fields.append(name)
    pt = getattr(portal_types, portal_type)
    behaviors = set(pt.behaviors)
    for behavior in behaviors:
        interface = nameToInterface(portal, behavior)
        fieldsets = mergedTaggedValueList(interface, FIELDSETS_KEY)
        for name, field in getFieldsInOrder(interface):
            if not fieldsets:
                fields.append(name)
            else:
                for fieldset in fieldsets:
                    fields = fields + list(fieldset.fields)
    # Remove duplicates
    fields = list(set(fields))
    # Set unicode
    return [safe_unicode(field) for field in fields]


def are_headers_in_fields(headers, plone_fields, portal_type):
    """ All headers field from CSV file should be a plone field
    portal_type used to log """
    exclude = ['id', 'id_parent']
    result = True
    for header in headers:
        if header not in exclude and header not in plone_fields:
            result = False
    return result

# -*- coding: utf-8 -*-
from collective.contact.importexport import _
from plone import api
from plone.app.textfield.value import RichTextValue
from plone.dexterity.interfaces import IDexterityFTI
from plone.directives import form
from plone.i18n.normalizer.interfaces import IURLNormalizer
from plone.namedfile.field import NamedFile
from Products.CMFPlone.utils import safe_unicode
from z3c.form import button
from zope import schema
from zope.component import getUtility
from zope.component.interface import nameToInterface
from zope.component.interfaces import ComponentLookupError
from zope.schema import getFieldsInOrder

import csv
import logging
import StringIO


logger = logging.getLogger('collective.contact.importexport import')
CONTACT_BASE_BEHAVIORS = [
    'collective.contact.core.behaviors.IContactDetails',
    'collective.contact.core.behaviors.IBirthday'
]

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
<h2>Organization</h2>
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
    <li>use_parent_address</li>
</ul>
If a header match with a organization field, it will be added in this field.

<h2>Person</h2>
You can import person from a csv file. This file should contains headers:
<ul>
  <li>additional_address_details</li>
  <li>cell_phone</li>
  <li>city</li>
  <li>country</li>
  <li>email</li>
  <li>fax</li>
  <li>firstname</li>
  <li>gender</li>
  <li>lastname</li>
  <li>number</li>
  <li>parent_address</li>
  <li>person_title</li>
  <li>phone</li>
  <li>region</li>
  <li>street</li>
  <li>title</li>
  <li>use_parent_address</li>
  <li>website</li>
  <li>zip_code</li>
</ul>
</p>
""")


def to_string(value):
    return safe_unicode(value)


def to_bool(value):
    return value.lower() in ('yes', 'true', 't', '1')


def to_int(value):
    if not value:
        return u''
    return int(value)


def to_float(value):
    if not value:
        return u''
    return float(value)


mapping_field_type = {
    'NamedImage': to_string,
    'Text': to_string,
    'Choice': to_string,
    'MasterSelectBoolField': to_bool,
    'TextLine': to_string,
    'RichText': to_string,
    'Int': to_int,
    'Float': to_float,
}


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
        title=_(u'Organizations file'),
        description=_(u'Import csv organizations file'),
        required=False
    )
    persons_file = NamedFile(
        title=_(u'Persons file'),
        description=_(u'Import csv persons file'),
        required=False
    )
    # functions_file = NamedFile(
    #     title=_(u"Functions file"),
    #     description=_(u'Import csv functions file'),
    #     required=False
    # )
    # occupied_functions_file = NamedFile(
    #     title=_(u"Occupied functions file"),
    #     description=_(u'Import csv occupied functions file'),
    #     required=False
    # )


def get_title(contents):
    keys = contents.keys()
    if 'title' in keys:
        return contents.get('title')
    elif 'firstname' in keys and 'lastname' in keys:
        firstname = contents['firstname']
        lastname = contents['lastname']
        title = u' '.join([x for x in (firstname, lastname) if x])
        return title
    else:
        return None


class ImportForm(form.SchemaForm):
    """ Define Form handling """
    name = _(u'Import contacts')
    schema = IImportForm
    ignoreContext = True

    label = u'Import contacts from CSV files'

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

        def get_cell(row, name, field_type):
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
                if field_type in mapping_field_type.keys():
                    return mapping_field_type[field_type](
                        row[index].decode('utf-8'))
                else:
                    return safe_unicode(row[index].decode('utf-8'))

        fields = get_all_fields_from(portal_type, self.context)
        updated = 0
        for row in data:
            contents = {}
            # Parse csv
            for head in headers:
                if head in fields.keys():
                    contents[head] = get_cell(
                        row,
                        safe_unicode(head),
                        fields[head]
                    )
                # else:
                #     activity.append(get_cell(
                #         row,
                #         safe_unicode(head),
                #         'TextLine'
                #     ))

            # Add into Plone and not get empty lines/title of cs
            title = get_title(contents)
            if title:
                utility = getUtility(IURLNormalizer)
                safe_id = utility.normalize(title)
                if safe_id not in self.context.contentIds():
                    self.context.invokeFactory(
                        portal_type,
                        safe_id,
                        title=title,
                        safe_id=safe_id,
                        street=contents.get('street', None),
                        number=contents.get('number', None),
                        zip_code=contents.get('zip_code', None),
                        city=contents.get('city', None)
                    )
                    obj = self.context[safe_id]
                    for key, value in contents.items():
                        if key == 'activity':
                            activity = ['<p>']
                            activity.append(value)
                            activity.append(u'</p>')
                            obj.activity = RichTextValue(u' '.join(activity))
                        else:
                            setattr(obj, key, value)

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
                        title.encode('utf8'))
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

        if data.get('persons_file'):
            persons_file = data['persons_file'].data
            number = self.process_csv(persons_file, 'person')
            if number is not None:
                self.status = "File uploaded. {} new persons created.".format(number)  # noqa

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


def get_all_fields_from(portal_type, context):
    portal_types = api.portal.get_tool('portal_types')
    schema = getUtility(IDexterityFTI, name=portal_type).lookupSchema()
    fields = {}
    for name, field in getFieldsInOrder(schema):
        if name not in fields.keys():
            fields[safe_unicode(name)] = field.__class__.__name__
    pt = getattr(portal_types, portal_type)
    behaviors = set(pt.behaviors)
    for contact_base_behavior in CONTACT_BASE_BEHAVIORS:
        if contact_base_behavior not in behaviors:
            behaviors.add(contact_base_behavior)
    for behavior in behaviors:
        try:
            interface = nameToInterface(context, behavior)
            for name, field in getFieldsInOrder(interface):
                if name not in fields.keys():
                    fields[safe_unicode(name)] = field.__class__.__name__
        except ComponentLookupError:
            pass
    return fields

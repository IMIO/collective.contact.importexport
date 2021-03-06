# -*- coding: utf-8 -*-

from plone import api
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller"""
        return [
            'collective.contact.importexport:uninstall',
        ]


def post_install(context):
    """Post install script"""
    # Do something at the end of the installation of this package.

    if not api.portal.get_registry_record('collective.contact.importexport.interfaces.IPipelineConfiguration.pipeline'):
        api.portal.set_registry_record(
            'collective.contact.importexport.interfaces.IPipelineConfiguration.pipeline', u"""[transmogrifier]
pipeline =
    initialization
    csv_disk_source
#    csv_ssh_source
    csv_reader
    common_input_checks
# personal input bp came here
    dependencysorter
    relationsinserter
#    stop
    updatepathinserter
    parentpathinserter
    moveobject
    pathinserter
    constructor
# personal attributes bp came here
    schemaupdater
    reindexobject
#    transitions_inserter
#    workflowupdater
#    breakpoint
    short_log
#    logger
    lastsection

# mandatory section !
[config]
# if empty, first found directory is used. Else relative path in portal
directory_path =
csv_encoding =
organizations_filename = organizations-test.csv
organizations_fieldnames = _id _oid title description organization_type use_parent_address street number additional_address_details zip_code city phone cell_phone fax email website region country _uid
persons_filename = persons-test.csv
persons_fieldnames = _id lastname firstname gender person_title birthday use_parent_address street number additional_address_details zip_code city phone cell_phone fax email website region country _uid
held_positions_filename = heldpositions-test.csv
held_positions_fieldnames = _id _pid _oid _fid label start_date end_date use_parent_address street number additional_address_details zip_code city phone cell_phone fax email website region country _uid
raise_on_error = 1

[initialization]
blueprint = collective.contact.importexport.init
# basepath is an absolute directory. If empty, buildout dir will be used
basepath =
# if subpath, it will be appended to basepath
subpath = imports

[csv_ssh_source]
blueprint = collective.contact.importexport.csv_ssh_source
servername = sftp-client.imio.be
username = zope
server_path = /srv/sftp/inbw/upload_success
registry_filename = 0_registry.dump
transfer_path =

[csv_disk_source]
blueprint = collective.contact.importexport.csv_disk_source
organizations_filename = ${config:organizations_filename}
persons_filename = ${config:persons_filename}
held_positions_filename = ${config:held_positions_filename}

[csv_reader]
blueprint = collective.contact.importexport.csv_reader
fmtparam-strict = python:True
csv_headers = python:True
raise_on_error = ${config:raise_on_error}

[common_input_checks]
blueprint = collective.contact.importexport.common_input_checks
phone_country = BE
language = fr
organization_uniques = _uid
organization_booleans = use_parent_address
person_uniques = _uid
person_booleans = use_parent_address
held_position_uniques = _uid
held_position_booleans = use_parent_address
raise_on_error = ${config:raise_on_error}

[dependencysorter]
blueprint = collective.contact.importexport.dependencysorter

[relationsinserter]
blueprint = collective.contact.importexport.relationsinserter
raise_on_error = ${config:raise_on_error}

[updatepathinserter]
blueprint = collective.contact.importexport.updatepathinserter
# list of 'column' 'index name' 'item condition' 'must-exist' quartets used to search in catalog for an existing object
organization_uniques = _uid UID python:True python:True
person_uniques = _uid UID python:True python:True
held_position_uniques = _uid UID python:True python:True
raise_on_error = ${config:raise_on_error}

[parentpathinserter]
blueprint = collective.contact.importexport.parentpathinserter
raise_on_error = ${config:raise_on_error}

[moveobject]
blueprint = collective.contact.importexport.moveobject
raise_on_error = ${config:raise_on_error}

[pathinserter]
blueprint = collective.contact.importexport.pathinserter
organization_id_keys = title
person_id_keys = firstname lastname
held_position_id_keys = label
raise_on_error = ${config:raise_on_error}

[constructor]
blueprint = collective.transmogrifier.sections.constructor

[schemaupdater]
blueprint = transmogrify.dexterity.schemaupdater

[reindexobject]
blueprint = plone.app.transmogrifier.reindexobject

[transitions_inserter]
blueprint = collective.contact.importexport.transitions_inserter

[workflowupdater]
blueprint = plone.app.transmogrifier.workflowupdater

[short_log]
blueprint = collective.contact.importexport.short_log

[logger]
blueprint = collective.transmogrifier.sections.logger
name = logger
level = INFO

[lastsection]
blueprint = collective.contact.importexport.lastsection
send_mail = 1

[stop]
blueprint = collective.contact.importexport.stop
condition = python:True

[breakpoint]
blueprint = collective.contact.importexport.breakpoint
condition = python:item.get('_id', u'') == u'0'
""")  # noqa: E501


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.

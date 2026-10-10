from collective.contact.core.interfaces import IContactable
from collective.contact.importexport.scripts.execute_pipeline import execute_pipeline
from collective.contact.importexport.tests.base import PipelineTestCase
from collective.transmogrifier.transmogrifier import configuration_registry
from datetime import date
from email import message_from_string
from email.header import decode_header
from email.header import make_header
from plone import api

import os


DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "hierarchy")
# default pipeline with the transitions of inactive contents
SECTIONS = [
    "initialization",
    "csv_disk_source",
    "csv_reader",
    "common_input_checks",
    "dependencysorter",
    "relationsinserter",
    "updatepathinserter",
    "parentpathinserter",
    "moveobject",
    "pathinserter",
    "constructor",
    "schemaupdater",
    "reindexobject",
    "transitions_inserter",
    "workflowupdater",
    "short_log",
    "lastsection",
]
REPLACEMENTS = {
    "directory_path =": "directory_path = mydirectory",
    "organizations_fieldnames = _id": "organizations_fieldnames = _inactive _id",
    "organization_booleans = use_parent_address": "organization_booleans = use_parent_address _inactive",
}


def data_files():
    """Returns the hierarchy csv files contents."""
    files = {}
    for filename in ("organizations.csv", "persons.csv", "held_positions.csv"):
        with open(os.path.join(DATA_DIR, filename), encoding="utf-8") as data_file:
            files[filename] = data_file.read()
    return files


def read_log(directory, filename):
    with open(os.path.join(directory, filename), encoding="utf-8") as log_file:
        return log_file.read()


class TestExecutePipeline(PipelineTestCase):

    def test_execute_pipeline(self):
        organizations = [{"_id": "1", "title": "Commune", "organization_type": "Commune"}]
        filepath = self.prepare_pipeline(organizations=organizations)
        execute_pipeline(self.portal, filepath)
        self.assertEqual(self.directory["commune"].title, "Commune")
        # configuration is registered once
        execute_pipeline(self.portal, filepath)
        self.assertEqual(self.directory["commune-1"].title, "Commune")

        # a missing csv file stops the pipeline: an email reports the error
        configuration_registry.clear()
        mailhost = self.setup_mailhost()
        api.portal.set_registry_record(
            "collective.contact.importexport.interfaces.IPipelineConfiguration.emails", "dest@example.com"
        )
        filepath = self.prepare_pipeline(replacements={"organizations.csv": "unknown.csv"}, organizations=[])
        with self.assertRaisesRegex(Exception, "Cannot open file"):
            execute_pipeline(self.portal, filepath)
        self.assertEqual(len(mailhost.messages), 1)
        message = message_from_string(mailhost.messages[0].decode())
        self.assertEqual(str(make_header(decode_header(message["Subject"]))), "Contact import report")
        text = message.get_payload()[0].get_payload()[1].get_payload(decode=True).decode()
        self.assertIn("Critical error during pipeline", text)
        # import of an organization hierarchy, persons and held positions
        configuration_registry.clear()
        filepath = self.prepare_pipeline(sections=SECTIONS, files=data_files(), replacements=REPLACEMENTS)
        execute_pipeline(self.portal, filepath)
        imio = self.directory["imio"]
        logiciels = imio["departement-logiciels"]
        courrier = logiciels["cellule-courrier"]
        self.assertEqual(
            (imio.title, imio.zip_code, imio.city, imio.phone, imio.email),
            ("IMIO", "5032", "Isnes", "081586100", "contact@imio.be"),
        )
        self.assertEqual((courrier.title, courrier.description), ("Cellule Courrier", "Gestion du courrier"))
        self.assertIn({"name": "Intercommunale", "token": "intercommunale"}, self.directory.organization_types)
        self.assertIn({"name": "Cellule", "token": "cellule"}, self.directory.organization_levels)
        # sub organizations use the parent address
        self.assertTrue(courrier.use_parent_address)
        details = IContactable(courrier).get_contact_details()
        self.assertEqual((details["address"]["city"], details["email"]), ("Isnes", "courrier@imio.be"))
        # inactive organizations are deactivated
        self.assertEqual(api.content.get_state(imio["service-formations"]), "deactivated")
        self.assertEqual(api.content.get_state(courrier), "active")
        # held positions are added in persons and linked to organizations
        jean = self.directory["jean-dupont"]
        self.assertEqual((jean.gender, jean.birthday, jean.cell_phone), ("M", date(1975, 4, 12), "0476123456"))
        self.assertEqual(
            [(pos.label, pos.position.to_object) for pos in jean.objectValues()], [("Agent courrier", courrier)]
        )
        self.assertEqual(
            [(pos.label, pos.position.to_object) for pos in self.directory["marie-lambert"].objectValues()],
            [("Directrice générale", imio)],
        )
        self.assertEqual(read_log(self.tmpdir, "ie_input_errors.log"), "")
        self.assertIn(
            "'O' => (nb=4, N=4, U=0, D=0, e=0), 'P' => (nb=2, N=2, U=0, D=0, e=0), "
            "'HP' => (nb=2, N=2, U=0, D=0, e=0)",
            read_log(self.tmpdir, "ie_shortlog.log"),
        )

    def test_execute_pipeline_update(self):
        """A second import with the uids updates the contents."""
        filepath = self.prepare_pipeline(
            sections=SECTIONS, files=data_files(), replacements=REPLACEMENTS, filename="pipeline.cfg"
        )
        execute_pipeline(self.portal, filepath)
        imio = self.directory["imio"]
        courrier = imio["departement-logiciels"]["cellule-courrier"]
        jean = self.directory["jean-dupont"]
        # the second import finds the contents by uid: they are updated, moved and deactivated
        organizations = [
            {
                "_id": "1",
                "title": "IMIO",
                "organization_type": "Intercommunale",
                "use_parent_address": "False",
                "zip_code": "5030",
                "city": "Gembloux",
                "_uid": api.content.get_uuid(imio),
                "_inactive": "False",
            },
            {
                "_id": "3",
                "_oid": "1",
                "title": "Cellule Courrier",
                "organization_type": "Cellule",
                "use_parent_address": "True",
                "_uid": api.content.get_uuid(courrier),
                "_inactive": "True",
            },
        ]
        persons = [
            {
                "_id": "1",
                "lastname": "Dupont",
                "firstname": "Jean",
                "use_parent_address": "False",
                "email": "jean.dupont@imio.be",
                "_uid": api.content.get_uuid(jean),
            }
        ]
        held_positions = [
            {
                "_id": "1",
                "_pid": "1",
                "_oid": "3",
                "label": "Responsable courrier",
                "use_parent_address": "True",
                "_uid": api.content.get_uuid(jean.objectValues()[0]),
            }
        ]
        self.prepare_pipeline(
            sections=SECTIONS,
            organizations=organizations,
            persons=persons,
            held_positions=held_positions,
            replacements=REPLACEMENTS,
            filename="pipeline.cfg",
        )
        execute_pipeline(self.portal, filepath)
        self.assertEqual((imio.zip_code, imio.city), ("5030", "Gembloux"))
        self.assertNotIn("cellule-courrier", imio["departement-logiciels"])
        self.assertEqual(api.content.get_state(imio["cellule-courrier"]), "deactivated")
        self.assertEqual(jean.email, "jean.dupont@imio.be")
        self.assertEqual(
            [(pos.label, pos.position.to_object) for pos in jean.objectValues()],
            [("Responsable courrier", imio["cellule-courrier"])],
        )
        self.assertIn(
            "'O' => (nb=2, N=0, U=2, D=0, e=0), 'P' => (nb=1, N=0, U=1, D=0, e=0), "
            "'HP' => (nb=1, N=0, U=1, D=0, e=0)",
            read_log(self.tmpdir, "ie_shortlog.log"),
        )

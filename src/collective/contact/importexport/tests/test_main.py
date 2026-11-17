from collective.contact.importexport import e_logger
from collective.contact.importexport import o_logger
from collective.contact.importexport.blueprints.main import ANNOTATION_KEY
from collective.contact.importexport.tests.base import PipelineTestCase
from datetime import date
from plone import api
from zope.annotation.interfaces import IAnnotations

import os


def read_log(directory, filename):
    with open(os.path.join(directory, filename), encoding="utf-8") as log_file:
        return log_file.read()


class TestInitialization(PipelineTestCase):

    def test_initialization(self):
        items = self.run_pipeline(last_section="initialization")
        self.assertEqual(items, [])
        annot = IAnnotations(self.portal)[ANNOTATION_KEY]
        self.assertEqual(annot["wp"], self.tmpdir)
        # log files are created in working path
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "ie_input_errors.log")))
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "ie_shortlog.log")))
        self.assertFalse(os.path.exists(os.path.join(self.tmpdir, "ie_input_errors_commit.log")))
        # commit log files are created when requested
        self.portal.REQUEST.set("_pipeline_commit_", True)
        self.run_pipeline(last_section="initialization")
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "ie_input_errors_commit.log")))
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "ie_shortlog_commit.log")))
        # directory is searched when no path is given, a wrong path is an error
        self.run_pipeline(
            last_section="initialization", replacements={"directory_path =": "directory_path = mydirectory"}
        )
        with self.assertRaisesRegex(Exception, "Directory not found"):
            self.run_pipeline(
                last_section="initialization", replacements={"directory_path =": "directory_path = nothing"}
            )

    def test_initialization_log_handlers(self):
        """The log file handlers of the previous imports are removed: lines are written once."""
        self.run_pipeline(organizations=[{"_id": "1", "title": "Commune", "organization_type": "Commune"}])
        self.run_pipeline(organizations=[{"_id": "1", "title": "CPAS", "organization_type": "CPAS"}])
        self.assertEqual(read_log(self.tmpdir, "ie_shortlog.log").count("'O' =>"), 1)


class TestCommonInputChecks(PipelineTestCase):

    def test_common_input_checks(self):
        organizations = [
            {
                "_id": "1",
                "title": " Commune ",
                "organization_type": "Commune",
                "use_parent_address": "False",
                "zip_code": "B-1000",
                "phone": "02/345.67.89",
                "email": "Contact@Commune.BE",
                "country": "Belgique",
            },
            {
                "_id": "2",
                "_oid": "1",
                "title": "Service",
                "organization_type": "",
                "use_parent_address": "true",
                "description": "Line 1\n",
            },
        ]
        persons = [
            {
                "_id": "1",
                "lastname": "Dupont",
                "firstname": "Jean",
                "gender": "M",
                "birthday": "1980/05/17",
                "use_parent_address": "False",
                "country": "France",
                "zip_code": "75001",
                "phone": "+33 1 42 68 53 00",
            }
        ]
        held_positions = [
            {
                "_id": "1",
                "_pid": "1",
                "_oid": "1",
                "label": "Mayor",
                "start_date": "2020/01/01",
                "end_date": "",
                "use_parent_address": "False",
            }
        ]
        items = self.run_pipeline(
            last_section="common_input_checks",
            organizations=organizations,
            persons=persons,
            held_positions=held_positions,
        )
        org1, org2, pers, pos = items
        self.assertEqual(org1["title"], "Commune")  # stripped
        self.assertEqual(org1["_parent"], "mydirectory")
        self.assertEqual(org1["organization_type"], "commune")  # token of the new type
        self.assertIs(org1["use_parent_address"], False)
        self.assertEqual(org1["zip_code"], "1000")
        self.assertEqual(org1["phone"], "023456789")
        self.assertEqual(org1["email"], "contact@commune.be")
        self.assertNotIn("_error", org1)
        self.assertIs(org2["use_parent_address"], True)
        self.assertEqual(org2["organization_type"], "corps")  # first level value
        self.assertEqual(pers["birthday"], date(1980, 5, 17))
        self.assertEqual(pers["gender"], "M")
        self.assertEqual(pers["phone"], "33142685300")
        self.assertIsNone(pos["_fid"])
        self.assertEqual(pos["start_date"], date(2020, 1, 1))
        self.assertIsNone(pos["end_date"])

        # errors are logged and flagged when pipeline does not raise
        no_raise = {"raise_on_error = 1": "raise_on_error = 0"}
        organizations = [
            {
                "_id": "1",
                "title": "First",
                "organization_type": "Commune",
                "use_parent_address": "False",
                "_uid": "abc",
            },
            {
                "_id": "1",
                "title": "Duplicated id",
                "organization_type": "Commune",
                "use_parent_address": "False",
                "_uid": "abc",
            },
            {"title": "No id", "use_parent_address": "False"},
            {"_id": "3", "_oid": "3", "title": "Own parent", "use_parent_address": "False"},
        ]
        persons = [
            {"_id": "1", "lastname": "Dupont", "gender": "X", "birthday": "not a date", "use_parent_address": "False"}
        ]
        held_positions = [
            {"_id": "1", "_oid": "1", "label": "No person", "use_parent_address": "False"},
            {"_id": "2", "_pid": "1", "label": "No organization", "use_parent_address": "False"},
        ]
        items = self.run_pipeline(
            last_section="common_input_checks",
            organizations=organizations,
            persons=persons,
            held_positions=held_positions,
            replacements=no_raise,
        )
        self.assertEqual(
            [(item["_type"], item["_id"]) for item in items],
            [("organization", "1"), ("organization", "1"), ("person", "1")],
        )
        self.assertEqual([item.get("_error", False) for item in items], [False, True, True])
        self.assertEqual(items[2]["gender"], "")
        log = read_log(self.tmpdir, "ie_input_errors.log")
        for message in (
            "duplicated id '1'",
            "duplicated _uid 'abc'",
            "missing id '_id'",
            "_oid is equal to _id",
            "missing related person id",
            "missing organization/position id",
        ):
            self.assertIn(message, log)

        # errors can raise exceptions
        for rows, message in (
            ({"organizations": [{"title": "No id"}]}, "Missing id"),
            ({"organizations": [{"_id": "1", "title": "A"}, {"_id": "1", "title": "B"}]}, "Duplicated id"),
            ({"organizations": [{"_id": "1", "_oid": "1", "title": "A"}]}, "Inconsistent _oid"),
            ({"held_positions": [{"_id": "1", "_oid": "1"}]}, "Missing _pid"),
            ({"held_positions": [{"_id": "1", "_pid": "1"}]}, "Missing _oid/_fid"),
        ):
            with self.assertRaisesRegex(Exception, message):
                self.run_pipeline(last_section="common_input_checks", **rows)

        # newlines replaced by hyphens and enterprise number cleaned
        replacements = {
            "organizations_fieldnames = _id": "organizations_fieldnames = enterprise_number _id",
            "organization_booleans =": "organization_hyphen_newline = title street\norganization_booleans =",
        }
        organizations = [
            {
                "enterprise_number": "BE 0123.456.749",
                "_id": "1",
                "title": "IMIO\nIntercommunale",
                "street": "Rue Léon Morel\n\n",
                "organization_type": "Intercommunale",
            }
        ]
        items = self.run_pipeline(
            last_section="common_input_checks", organizations=organizations, replacements=replacements
        )
        self.assertEqual(
            (items[0]["title"], items[0]["street"], items[0]["enterprise_number"]),
            ("IMIO - Intercommunale", "Rue Léon Morel", "BE0123456749"),
        )

    def test_common_input_checks_default_encoding(self):
        """The empty csv_encoding of the default pipeline reads utf-8."""
        items = self.run_pipeline(
            last_section="common_input_checks",
            replacements={"csv_encoding =": "csv_encoding ="},
            organizations=[{"_id": "1", "title": "Liège", "organization_type": "Commune"}],
        )
        self.assertEqual(items[0]["title"], "Liège")


class TestRelationsInserter(PipelineTestCase):

    def test_relations_inserter(self):
        organizations = [{"_id": "1", "title": "Commune", "organization_type": "Commune"}]
        persons = [{"_id": "1", "lastname": "Dupont", "firstname": "Jean"}]
        held_positions = [{"_id": "1", "_pid": "1", "_oid": "1", "label": "Mayor"}]
        self.run_pipeline(organizations=organizations, persons=persons, held_positions=held_positions)
        organization = self.directory["commune"]
        position = self.directory["jean-dupont"]["mayor-commune"]
        self.assertEqual(position.position.to_object, organization)
        # unknown organization
        no_raise = {"raise_on_error = 1": "raise_on_error = 0"}
        held_positions = [{"_id": "1", "_pid": "1", "_oid": "99", "label": "Lost"}]
        items = self.run_pipeline(
            last_section="relationsinserter", persons=persons, held_positions=held_positions, replacements=no_raise
        )
        self.assertEqual([item["_type"] for item in items], ["person"])
        self.assertIn("invalid related organization id '99'", read_log(self.tmpdir, "ie_input_errors.log"))
        with self.assertRaisesRegex(Exception, "Cannot find _oid"):
            self.run_pipeline(last_section="relationsinserter", persons=persons, held_positions=held_positions)


class TestUpdatePathInserter(PipelineTestCase):

    def test_update_path_inserter(self):
        self.run_pipeline(organizations=[{"_id": "1", "title": "Commune", "organization_type": "Commune"}])
        organization = self.directory["commune"]
        # searching an existing object by uid gives an update
        items = self.run_pipeline(
            last_section="updatepathinserter",
            organizations=[{"_id": "1", "title": "New title", "_uid": api.content.get_uuid(organization)}],
        )
        self.assertEqual((items[-1]["_act"], items[-1]["_path"]), ("update", "mydirectory/commune"))
        # nothing found but must exist
        no_raise = {"raise_on_error = 1": "raise_on_error = 0"}
        items = self.run_pipeline(
            last_section="updatepathinserter",
            replacements=no_raise,
            organizations=[{"_id": "1", "title": "New title", "_uid": "unknown"}],
        )
        self.assertNotIn("_path", items[-1])
        self.assertTrue(items[-1]["_error"])
        self.assertIn("doesn't get any result", read_log(self.tmpdir, "ie_input_errors.log"))
        with self.assertRaisesRegex(Exception, "Must find something"):
            self.run_pipeline(
                last_section="updatepathinserter", organizations=[{"_id": "1", "title": "New title", "_uid": "unknown"}]
            )
        # multiple results
        uniques = "organization_uniques = _uid UID python:True python:True"
        self.run_pipeline(organizations=[{"_id": "1", "title": "Commune", "organization_type": "Commune"}])
        self.assertEqual(len([oid for oid in self.directory.objectIds() if oid.startswith("commune")]), 2)
        with self.assertRaisesRegex(Exception, "Too more results"):
            self.run_pipeline(
                last_section="updatepathinserter",
                replacements={uniques: "organization_uniques = title Title python:True python:True"},
                organizations=[{"_id": "1", "title": "Commune"}],
            )
        # wrong option
        with self.assertRaisesRegex(Exception, "multiple of 4"):
            self.run_pipeline(
                last_section="updatepathinserter", replacements={uniques: "organization_uniques = _uid UID"}
            )
        # a search on internal_number needs the collective.behavior.internalnumber behavior
        with self.assertRaisesRegex(Exception, "The internalnumber behavior is not defined on type organization"):
            self.run_pipeline(
                last_section="updatepathinserter",
                organizations=[
                    {"internal_number": "ORG-1", "_id": "1", "title": "Commune", "organization_type": "Commune"}
                ],
                replacements={
                    "organizations_fieldnames = _id": "organizations_fieldnames = internal_number _id",
                    uniques: "organization_uniques = internal_number internal_number python:True python:False",
                },
            )


class TestParentPathInserter(PipelineTestCase):

    def test_parent_path_inserter(self):
        organizations = [
            {"_id": "1", "title": "Commune", "organization_type": "Commune"},
            {"_id": "2", "_oid": "1", "title": "Service", "organization_type": "Service"},
        ]
        persons = [{"_id": "1", "lastname": "Dupont", "firstname": "Jean"}]
        held_positions = [{"_id": "1", "_pid": "1", "_oid": "2", "label": "Chief"}]
        self.run_pipeline(organizations=organizations, persons=persons, held_positions=held_positions)
        self.assertEqual(self.directory["commune"]["service"].portal_type, "organization")
        self.assertEqual(self.directory["jean-dupont"]["chief-commune-service"].portal_type, "held_position")
        # unknown parent organization and person
        no_raise = {"raise_on_error = 1": "raise_on_error = 0"}
        items = self.run_pipeline(
            last_section="parentpathinserter",
            replacements=no_raise,
            organizations=[{"_id": "2", "_oid": "99", "title": "Orphan"}],
            persons=persons,
            held_positions=[{"_id": "1", "_pid": "99", "_oid": "", "_fid": ""}],
        )
        self.assertEqual([item["_type"] for item in items], ["person"])
        log = read_log(self.tmpdir, "ie_input_errors.log")
        self.assertIn("invalid parent organization id '99'", log)
        self.assertIn("missing organization/position id", log)
        with self.assertRaisesRegex(Exception, "Cannot find parent"):
            self.run_pipeline(
                last_section="parentpathinserter", organizations=[{"_id": "2", "_oid": "99", "title": "x"}]
            )


class TestMoveObject(PipelineTestCase):

    def test_move_object(self):
        organizations = [
            {"_id": "1", "title": "Commune", "organization_type": "Commune"},
            {"_id": "2", "title": "Service", "organization_type": "Service"},
        ]
        self.run_pipeline(organizations=organizations)
        commune = self.directory["commune"]
        service = self.directory["service"]
        # service is now a child of commune
        organizations = [
            {"_id": "1", "title": "Commune", "_uid": api.content.get_uuid(commune)},
            {"_id": "2", "_oid": "1", "title": "Service", "_uid": api.content.get_uuid(service)},
        ]
        items = self.run_pipeline(last_section="moveobject", organizations=organizations)
        self.assertNotIn("service", self.directory.objectIds())
        self.assertEqual(commune["service"].portal_type, "organization")
        self.assertEqual(items[-1]["_path"], "mydirectory/commune/service")
        # nothing to move when parent is the same
        items = self.run_pipeline(last_section="moveobject", organizations=organizations)
        self.assertEqual(items[-1]["_path"], "mydirectory/commune/service")
        self.assertEqual(commune["service"].portal_type, "organization")


class TestPathInserter(PipelineTestCase):

    def test_path_inserter(self):
        organizations = [
            {"_id": "1", "title": "Commune de Namur", "organization_type": "Commune"},
            {"_id": "2", "title": "Commune de Namur", "organization_type": "Commune"},
            {"_id": "3", "_oid": "1", "title": "Service", "organization_type": "Service"},
        ]
        persons = [{"_id": "1", "lastname": "Dupont", "firstname": "Jean"}]
        held_positions = [{"_id": "1", "_pid": "1", "_oid": "3", "label": "Chief"}]
        items = self.run_pipeline(organizations=organizations, persons=persons, held_positions=held_positions)
        # existing ids are not reused
        self.assertEqual(
            [(item["_act"], item["_path"]) for item in items[1:]],
            [
                ("new", "mydirectory/commune-de-namur"),
                ("new", "mydirectory/commune-de-namur-1"),
                ("new", "mydirectory/commune-de-namur/service"),
                ("new", "mydirectory/jean-dupont"),
                ("new", "mydirectory/jean-dupont/chief-commune-de-namur-service"),
            ],
        )
        # no usable title
        no_raise = {"raise_on_error = 1": "raise_on_error = 0"}
        items = self.run_pipeline(
            last_section="pathinserter", organizations=[{"_id": "1", "title": ""}], replacements=no_raise
        )
        self.assertEqual(items, [])
        self.assertIn("cannot get an id from id keys", read_log(self.tmpdir, "ie_input_errors.log"))
        with self.assertRaisesRegex(Exception, "No title"):
            self.run_pipeline(last_section="pathinserter", organizations=[{"_id": "1", "title": ""}])


class TestTransitionsInserter(PipelineTestCase):

    def test_transitions_inserter(self):
        sections = [
            "initialization",
            "csv_disk_source",
            "csv_reader",
            "common_input_checks",
            "dependencysorter",
            "updatepathinserter",
            "parentpathinserter",
            "pathinserter",
            "constructor",
            "schemaupdater",
            "transitions_inserter",
        ]
        replacements = {
            "organizations_fieldnames = _id": "organizations_fieldnames = _inactive _id",
            "organization_booleans = use_parent_address": "organization_booleans = use_parent_address _inactive",
        }
        organizations = [
            {"_id": "1", "title": "Active", "organization_type": "Commune", "_inactive": "False"},
            {"_id": "2", "title": "Inactive", "organization_type": "Commune", "_inactive": "True"},
        ]
        items = self.run_pipeline(sections=sections, organizations=organizations, replacements=replacements)
        organization_items = [item for item in items if item["_type"] == "organization"]
        self.assertNotIn("_transitions", organization_items[0])
        self.assertEqual(organization_items[1]["_transitions"], "deactivate")
        # a deactivated object is not activated
        deactivated = self.directory["inactive"]
        api.content.transition(deactivated, "deactivate")
        organizations = [
            {"_id": "2", "title": "Inactive", "_inactive": "False", "_uid": api.content.get_uuid(deactivated)}
        ]
        items = self.run_pipeline(sections=sections, organizations=organizations, replacements=replacements)
        self.assertNotIn("_transitions", items[-1])
        self.assertIn("current state is deactivated", read_log(self.tmpdir, "ie_input_errors.log"))
        # _inactive must be a boolean
        with self.assertRaisesRegex(Exception, "_inactive field is not configured as boolean"):
            self.run_pipeline(
                sections=sections,
                organizations=organizations,
                replacements={"organizations_fieldnames = _id": "organizations_fieldnames = _inactive _id"},
            )


class TestLastSection(PipelineTestCase):

    def test_last_section(self):
        mailhost = self.setup_mailhost()
        organizations = [
            {"_id": "1", "title": "Commune", "organization_type": "Commune", "phone": "0000"},
            {"_id": "2", "title": "Other", "organization_type": "Commune"},
        ]
        persons = [{"_id": "1", "lastname": "Dupont", "firstname": "Jean"}]
        with self.assertLogs(o_logger, level="INFO") as logs:
            with self.assertLogs(e_logger, level="ERROR"):
                self.run_pipeline(organizations=organizations, persons=persons)
        summary = [line for line in logs.output if "'O' =>" in line]
        self.assertEqual(len(summary), 1)
        self.assertIn("'O' => (nb=2, N=2, U=0, D=0, e=1), 'P' => (nb=1, N=1, U=0, D=0, e=0)", summary[0])
        self.assertEqual(len(mailhost.messages), 0)  # mail sending is not requested
        # a mail is sent with errors
        api.portal.set_registry_record(
            "collective.contact.importexport.interfaces.IPipelineConfiguration.emails", "dest@example.com"
        )
        with self.assertLogs(e_logger, level="ERROR"):
            self.run_pipeline(organizations=organizations[:1], replacements={"send_mail = 0": "send_mail = 1"})
        self.assertEqual(len(mailhost.messages), 1)
        self.assertIn("there are 1 items in error", mailhost.messages[0].decode())

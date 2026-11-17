from collective.contact.importexport import e_logger
from collective.contact.importexport.blueprints.main import ANNOTATION_KEY
from collective.contact.importexport.tests.base import PipelineTestCase
from collective.contact.importexport.utils import alphanum
from collective.contact.importexport.utils import digit
from collective.contact.importexport.utils import get_country_code
from collective.contact.importexport.utils import log_error
from collective.contact.importexport.utils import send_report
from collective.contact.importexport.utils import valid_email
from collective.contact.importexport.utils import valid_phone
from collective.contact.importexport.utils import valid_value_in_list
from collective.contact.importexport.utils import valid_zip
from email import message_from_string
from email.header import decode_header
from email.header import make_header
from plone import api
from zope.annotation.interfaces import IAnnotations

import os


class TestUtils(PipelineTestCase):
    """Tests utils.py functions. PipelineTestCase provides the portal, a temporary directory and a mailhost."""

    def setUp(self):
        super().setUp()
        self.item = {"_set": "set1", "_type": "organization", "_ln": 3}

    def test_log_error(self):
        with self.assertLogs(e_logger, level="ERROR") as logs:
            log_error(self.item, "a problem")
        self.assertEqual(logs.output, ["ERROR:ccie-input:set1: O, ln 3, a problem"])
        self.assertTrue(self.item["_error"])
        with self.assertLogs(e_logger, level="CRITICAL") as logs:
            log_error(self.item, "a critical problem", level="critical")
        self.assertEqual(logs.output, ["CRITICAL:ccie-input:set1: O, ln 3, a critical problem"])

    def test_digit(self):
        self.assertEqual(digit("02/123.45-67 x"), "021234567")
        self.assertEqual(digit(""), "")

    def test_alphanum(self):
        self.assertEqual(alphanum("BE 0123.456-789"), "BE0123456789")
        self.assertEqual(alphanum("--"), "")

    def test_get_country_code(self):
        item = {"country": "Belgique", "_set": "set1", "_type": "organization", "_ln": 3}
        self.assertEqual(get_country_code(item, "country", "BE", languages=("fr", "en")), "BE")
        item["country"] = "  GERMANY".strip()
        self.assertEqual(get_country_code(item, "country", "BE", languages=("fr", "en")), "DE")
        # accents are removed
        item["country"] = "Équateur"
        self.assertEqual(get_country_code(item, "country", "BE", languages=("fr", "en")), "EC")
        # empty country
        item["country"] = ""
        self.assertIsNone(get_country_code(item, "country", "BE"))
        self.assertNotIn("_error", item)
        # untranslatable country
        item["country"] = "Atlantis"
        with self.assertLogs(e_logger, level="ERROR"):
            self.assertEqual(get_country_code(item, "country", "BE", languages=("fr", "en")), "")
        self.assertTrue(item["_error"])

    def test_valid_zip(self):
        item = dict(self.item, zip="B-1000")
        # digits are kept for countries using digits
        self.assertEqual(valid_zip(item, "zip", "BE"), "1000")
        self.assertNotIn("_error", item)
        # default country is BE
        self.assertEqual(valid_zip(item, "zip", None), "1000")
        # empty zip
        self.assertEqual(valid_zip(dict(self.item, zip=""), "zip", "BE"), "")
        # zip not matching the country pattern is kept and logged
        item = dict(self.item, zip="10")
        with self.assertLogs(e_logger, level="ERROR") as logs:
            self.assertEqual(valid_zip(item, "zip", "BE"), "10")
        self.assertIn("doesn't match pattern", logs.output[0])
        self.assertTrue(item["_error"])
        # country without pattern
        item = dict(self.item, zip="1000")
        with self.assertLogs(e_logger, level="ERROR") as logs:
            self.assertEqual(valid_zip(item, "zip", "XX"), "1000")
        self.assertIn("can't check zip code", logs.output[0])
        # non digit country
        item = dict(self.item, zip="SW1A 1AA")
        self.assertEqual(valid_zip(item, "zip", "GB"), "SW1A 1AA")
        self.assertNotIn("_error", item)

    def test_valid_phone(self):
        item = dict(self.item, phone="02/345.67.89")
        self.assertEqual(valid_phone(item, "phone", "BE", "BE"), "023456789")
        # number of another country
        item = dict(self.item, phone="+33 1 42 68 53 00")
        self.assertEqual(valid_phone(item, "phone", "FR", "BE"), "33142685300")
        # empty
        self.assertEqual(valid_phone(dict(self.item, phone=""), "phone", "BE", "BE"), "")
        # country conversion problem
        item = dict(self.item, phone="023456789")
        with self.assertLogs(e_logger, level="ERROR") as logs:
            self.assertEqual(valid_phone(item, "phone", "", "BE"), "")
        self.assertIn("can't check phone", logs.output[0])
        # invalid number
        item = dict(self.item, phone="0000000")
        with self.assertLogs(e_logger, level="ERROR") as logs:
            self.assertEqual(valid_phone(item, "phone", "BE", "BE"), "")
        self.assertIn("is invalid", logs.output[0])
        # not parsable number
        item = dict(self.item, phone="1")
        with self.assertLogs(e_logger, level="ERROR") as logs:
            self.assertEqual(valid_phone(item, "phone", "BE", "BE"), "")
        self.assertIn("cannot be parsed", logs.output[0])
        self.assertTrue(item["_error"])

    def test_valid_email(self):
        item = dict(self.item, email=" Jean.Dupont@Example.COM; ")
        self.assertEqual(valid_email(item, "email"), "jean.dupont@example.com")
        self.assertNotIn("_error", item)
        self.assertEqual(valid_email(dict(self.item, email=" , "), "email"), "")
        item = dict(self.item, email="not an email")
        with self.assertLogs(e_logger, level="ERROR") as logs:
            self.assertEqual(valid_email(item, "email"), "")
        self.assertIn("email col 'email'", logs.output[0])
        self.assertTrue(item["_error"])

    def test_valid_value_in_list(self):
        self.assertEqual(valid_value_in_list(self.item, "F", ("", "F", "M")), "F")
        self.assertNotIn("_error", self.item)
        with self.assertLogs(e_logger, level="ERROR"):
            self.assertEqual(valid_value_in_list(self.item, "X", ("", "F", "M")), "")
        self.assertTrue(self.item["_error"])

    def test_send_report(self):
        mailhost = self.setup_mailhost()
        lines = ["First line", "Second line"]
        # no emails configured: nothing is sent
        send_report(self.portal, lines)
        self.assertEqual(len(mailhost.messages), 0)
        # emails configured
        api.portal.set_registry_record(
            "collective.contact.importexport.interfaces.IPipelineConfiguration.emails", "dest@example.com"
        )
        for filename in ("ie_input_errors.log", "ie_shortlog.log"):
            with open(os.path.join(self.tmpdir, filename), "w") as log_file:
                log_file.write("content of {}".format(filename))
        IAnnotations(self.portal)[ANNOTATION_KEY] = {"wp": self.tmpdir}
        send_report(self.portal, lines)
        self.assertEqual(len(mailhost.messages), 1)
        message = message_from_string(mailhost.messages[0].decode())
        self.assertEqual(message["To"], "dest@example.com")
        self.assertEqual(message["From"], "site@example.com")
        self.assertEqual(str(make_header(decode_header(message["Subject"]))), "Contact import report")
        self.assertEqual(
            [part.get_filename() for part in message.walk() if part.get_filename()],
            ["ie_input_errors.log", "ie_shortlog.log"],
        )

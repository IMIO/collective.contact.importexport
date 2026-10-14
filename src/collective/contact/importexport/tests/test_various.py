from collective.contact.importexport import o_logger
from collective.contact.importexport.tests.base import PipelineTestCase
from unittest import mock


class TestBreakpointSection(PipelineTestCase):

    def test_breakpoint_section(self):
        sections = ["initialization", "csv_disk_source", "csv_reader", "breakpoint"]
        replacements = {"python:item.get('_id', u'') == u'0'": "python:item.get('_id') == '2'"}
        organizations = [{"_id": "1", "title": "First"}, {"_id": "2", "title": "Second"}]
        # the debugger is an external tool: it is replaced to check the breakpoint is reached
        with mock.patch("builtins.breakpoint") as debugger:
            items = self.run_pipeline(sections=sections, organizations=organizations, replacements=replacements)
        self.assertEqual([item["_id"] for item in items], ["1", "2"])
        self.assertEqual(debugger.call_count, 1)


class TestShortLog(PipelineTestCase):

    def test_short_log(self):
        sections = ["initialization", "csv_disk_source", "csv_reader", "short_log"]
        with self.assertRaises(KeyError):  # _act is mandatory: set by the path sections
            self.run_pipeline(sections=sections, organizations=[{"_id": "1", "title": "First"}])
        # full pipeline
        with self.assertLogs(o_logger, level="INFO") as logs:
            self.run_pipeline(organizations=[{"_id": "1", "title": "First", "organization_type": "Commune"}])
        self.assertIn("O,1,N,mydirectory/first", "".join(logs.output).replace(" ", ""))


class TestStopSection(PipelineTestCase):

    def test_stop_section(self):
        sections = ["initialization", "csv_disk_source", "csv_reader", "stop"]
        organizations = [{"_id": "1", "title": "First"}]
        # condition is true
        with self.assertRaisesRegex(Exception, "STOP requested"):
            self.run_pipeline(sections=sections, organizations=organizations)
        # condition is false
        items = self.run_pipeline(
            sections=sections,
            organizations=organizations,
            replacements={"condition = python:True": "condition = python:False"},
        )
        self.assertEqual([item["_id"] for item in items], ["1"])

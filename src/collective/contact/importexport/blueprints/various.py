from collective.contact.importexport import A_S
from collective.contact.importexport import o_logger
from collective.contact.importexport import T_S
from collective.contact.importexport.blueprints.main import ANNOTATION_KEY
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import Condition
from imio.helpers.transmogrifier import key_val as shortcut
from zope.annotation.interfaces import IAnnotations
from zope.interface import implementer
from zope.interface import provider


@provider(ISectionBlueprint)
@implementer(ISection)
class BreakpointSection:
    """Stops in the debugger if condition is matched.

    Parameters:
        * condition = M, matching condition.
    """

    def __init__(self, transmogrifier, name, options, previous):
        condition = options["condition"]
        self.condition = Condition(condition, transmogrifier, name, options)
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)

    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                breakpoint()  # Break! (PYTHONBREAKPOINT can select the debugger)
            yield item


@provider(ISectionBlueprint)
@implementer(ISection)
class ShortLog:
    """Logs shortly item."""

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)

    def __iter__(self):
        for item in self.previous:
            to_print = "{}:{},{},{}, {}".format(
                item["_set"],
                shortcut(item["_type"], T_S),
                item.get("_id", ""),
                shortcut(item["_act"], A_S),
                item.get("_path", item.get("_del_path", "")),
            )
            # print(to_print, file=sys.stderr)
            o_logger.info(to_print)
            yield item


@provider(ISectionBlueprint)
@implementer(ISection)
class StopSection:
    """Stops if condition is matched.

    Parameters:
        * condition = M, matching condition.
    """

    def __init__(self, transmogrifier, name, options, previous):
        condition = options["condition"]
        self.condition = Condition(condition, transmogrifier, name, options)
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.storage = IAnnotations(transmogrifier).get(ANNOTATION_KEY)

    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                raise Exception("STOP requested")
            yield item

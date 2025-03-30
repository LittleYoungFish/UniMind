from .syntax_checker import SyntaxChecker
from .import_checker import ImportChecker
from .pylint_checker import PylintChecker
from .checker_pipeline import CheckerPipeline
from .attribute_checker import AttributeChecker

static_checkers = CheckerPipeline()
static_checkers.add_checker(
    SyntaxChecker(), ImportChecker(), AttributeChecker(), PylintChecker()
)

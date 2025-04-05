from .checker_pipeline import CheckerPipeline
from .python import SyntaxChecker, ImportChecker, AttributeChecker, PylintChecker

static_checkers = CheckerPipeline()
static_checkers.add_checker(
    SyntaxChecker(),
    ImportChecker(),
    # AttributeChecker(),
    PylintChecker(),
)

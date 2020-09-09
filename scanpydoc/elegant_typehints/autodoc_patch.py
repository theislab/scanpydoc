from functools import wraps
from typing import Mapping, Callable

from docutils.statemachine import StringList
from sphinx.ext.autodoc import ClassDocumenter


def dir_head_adder(
    qualname_overrides: Mapping[str, str],
    orig: Callable[[ClassDocumenter, str], None],
):
    @wraps(orig)
    def add_directive_header(self: ClassDocumenter, sig: str) -> None:
        orig(self, sig)
        lines: StringList = self.directive.result
        for old, new in qualname_overrides:
            lines.replace(f":class:`{old}`", f":class:`{new}`")

    return add_directive_header

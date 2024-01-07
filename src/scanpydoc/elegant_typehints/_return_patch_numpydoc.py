from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sphinx_autodoc_typehints import format_annotation


if TYPE_CHECKING:
    from collections.abc import Iterable, Generator

    from sphinx.ext.napoleon import NumpyDocstring  # type: ignore[attr-defined]

__all__ = ["_parse_returns_section"]


def _process_return(lines: Iterable[str]) -> Generator[str, None, None]:
    for line in lines:
        m = re.fullmatch(r"(?P<param>\w+)\s+:\s+(?P<type>[\w.]+)", line)
        if m:
            # TODO: pass in the object
            typ = format_annotation(m.group("type"))
            yield f'**{m["param"]}** : {typ}'
        else:
            yield line


def _parse_returns_section(self: NumpyDocstring, section: str) -> list[str]:  # noqa: ARG001
    lines_raw = list(_process_return(self._dedent(self._consume_to_next_section())))
    if lines_raw[0] == ":":
        # Remove the “:” inserted by sphinx-autodoc-typehints
        # https://github.com/tox-dev/sphinx-autodoc-typehints/blob/a5c091f725da8374347802d54c16c3d38833d41c/src/sphinx_autodoc_typehints/patches.py#L66
        lines_raw.pop(0)
    lines = self._format_block(":returns: ", lines_raw)
    if lines and lines[-1]:
        lines.append("")
    return lines

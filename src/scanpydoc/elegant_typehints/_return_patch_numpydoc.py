from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from sphinx.ext.napoleon import NumpyDocstring  # type: ignore[attr-defined]

__all__ = ["_parse_returns_section"]


def _parse_returns_section(self: NumpyDocstring, section: str) -> list[str]:  # noqa: ARG001
    lines_raw = list(self._dedent(self._consume_to_next_section()))
    if lines_raw[0] == ":":
        # Remove the “:” inserted by sphinx-autodoc-typehints
        # https://github.com/tox-dev/sphinx-autodoc-typehints/blob/a5c091f725da8374347802d54c16c3d38833d41c/src/sphinx_autodoc_typehints/patches.py#L66
        lines_raw.pop(0)
    lines = self._format_block(":returns: ", lines_raw)
    if lines and lines[-1]:
        lines.append("")
    return lines

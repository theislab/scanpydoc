from __future__ import annotations

import re
import sys
import inspect
from typing import TYPE_CHECKING, Union, get_args, get_origin, get_type_hints
from typing import Tuple as t_Tuple  # noqa: UP035
from logging import getLogger

from sphinx.ext.napoleon import NumpyDocstring  # type: ignore[attr-defined]
from sphinx_autodoc_typehints import format_annotation


if TYPE_CHECKING:
    from typing import Any
    from collections.abc import Sequence

    from sphinx.application import Sphinx
    from sphinx.ext.autodoc import Options


if sys.version_info > (3, 10):
    from types import UnionType

    UNION_TYPES = {Union, UnionType}
else:  # pragma: no cover
    UNION_TYPES = {Union}


__all__ = ["process_docstring", "_parse_returns_section", "setup"]

logger = getLogger(__name__)
re_ret = re.compile("^:returns?: ")


def get_tuple_annot(annotation: type | None) -> tuple[type, ...] | None:
    if annotation is None:
        return None
    origin = get_origin(annotation)
    if not origin:
        return None
    if origin in UNION_TYPES:
        for annot in get_args(annotation):
            origin = get_origin(annot)
            if origin in (tuple, t_Tuple):  # noqa: UP006
                annotation = annot
                break
        else:
            return None
    return get_args(annotation)


def process_docstring(  # noqa: PLR0913
    app: Sphinx,
    what: str,
    name: str,  # noqa: ARG001
    obj: Any,  # noqa: ANN401
    options: Options | None,  # noqa: ARG001
    lines: list[str],
) -> None:
    # Handle complex objects
    if isinstance(obj, property):
        obj = obj.fget
    if not callable(obj):
        return
    if what in ("class", "exception"):
        obj = obj.__init__
    obj = inspect.unwrap(obj)
    try:
        hints = get_type_hints(obj)
    except (AttributeError, NameError, TypeError):  # pragma: no cover
        # Introspecting a slot wrapper can raise TypeError
        return
    ret_types = get_tuple_annot(hints.get("return"))
    if ret_types is None:
        return

    idxs_ret_names = _get_idxs_ret_names(lines)
    if len(idxs_ret_names) == len(ret_types):
        for l, rt in zip(idxs_ret_names, ret_types):
            typ = format_annotation(rt, app.config)
            if (line := lines[l]).lstrip() in {":returns: :", ":return: :", ":"}:
                transformed = f"{line[:-1]}{typ}"
            else:
                transformed = f"{line} : {typ}"
            lines[l : l + 1] = [transformed]


def _get_idxs_ret_names(lines: Sequence[str]) -> list[int]:
    # Get return section
    i_prefix = None
    l_start = 0
    for l, line in enumerate(lines):
        if i_prefix is None:
            m = re_ret.match(line)
            if m:
                i_prefix = m.span()[1]
                l_start = l
        elif len(line[:i_prefix].strip()) > 0:
            l_end = l - 1
            break
    else:
        l_end = len(lines) - 1
    if i_prefix is None:
        return []

    # Meat
    idxs_ret_names = []
    for l, line in enumerate([l[i_prefix:] for l in lines[l_start : l_end + 1]]):
        if (line == ":" or line.isidentifier()) and (
            lines[l + l_start + 1].startswith("    ")
        ):
            idxs_ret_names.append(l + l_start)
    return idxs_ret_names


def _parse_returns_section(self: NumpyDocstring, section: str) -> list[str]:  # noqa: ARG001
    """Parse return section as prose instead of tuple by default."""
    lines_raw = list(self._dedent(self._consume_to_next_section()))
    lines = self._format_block(":returns: ", lines_raw)
    if lines and lines[-1]:
        lines.append("")
    return lines


def _delete_sphinx_autodoc_typehints_docstring_processor(app: Sphinx) -> None:
    for listener in app.events.listeners["autodoc-process-docstring"].copy():
        handler_name = getattr(listener.handler, "__name__", None)
        # https://github.com/tox-dev/sphinx-autodoc-typehints/blob/a5c091f725da8374347802d54c16c3d38833d41c/src/sphinx_autodoc_typehints/patches.py#L69
        if handler_name == "napoleon_numpy_docstring_return_type_processor":
            app.disconnect(listener.id)


def setup(app: Sphinx) -> None:
    """Patches the Sphinx app and :mod:`sphinx.ext.napoleon` in some ways.

    1. Replaces the return section parser of napoleon’s NumpyDocstring
       with one that just adds a prose section.
    2. Removes sphinx-autodoc-typehints’s docstring processor that expects
       NumpyDocstring’s old behavior.
    2. Adds our own docstring processor that adds tuple return types
       If the docstring contains a definition list of appropriate length.
    """
    NumpyDocstring._parse_returns_section = _parse_returns_section  # type: ignore[method-assign,assignment]  # noqa: SLF001
    _delete_sphinx_autodoc_typehints_docstring_processor(app)
    app.connect("autodoc-process-docstring", process_docstring, 1000)

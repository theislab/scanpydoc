from __future__ import annotations

import inspect
import re
from collections.abc import Collection
from logging import getLogger
from typing import TYPE_CHECKING, Any, get_args, get_origin, get_type_hints

from ._formatting import format_both


if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.ext.autodoc import Options


logger = getLogger(__name__)
re_ret = re.compile("^:returns?: ")


def get_tuple_annot(annotation: type | None) -> tuple[type, ...] | None:
    from typing import Union

    if annotation is None:
        return None
    origin = get_origin(annotation)
    if not origin:
        return None
    if origin is Union:
        for annot in get_args(annotation):
            origin = get_origin(annot)
            if origin in (tuple, tuple):
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
    except (AttributeError, NameError, TypeError):
        # Introspecting a slot wrapper will raise TypeError
        return
    ret_types = get_tuple_annot(hints.get("return"))
    if ret_types is None:
        return

    idxs_ret_names = _get_idxs_ret_names(lines)
    if len(idxs_ret_names) == len(ret_types):
        for l, rt in zip(idxs_ret_names, ret_types):
            typ = format_both(rt, app.config)
            lines[l : l + 1] = [f"{lines[l]} : {typ}"]


def _get_idxs_ret_names(lines: Collection[str]) -> list[int]:
    # Get return section
    i_prefix = None
    l_start = None
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
        if line.isidentifier() and lines[l + l_start + 1].startswith("    "):
            idxs_ret_names.append(l + l_start)
    return idxs_ret_names

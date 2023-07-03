from __future__ import annotations

import inspect
import re
from logging import getLogger
from typing import Any, get_args, get_origin, get_type_hints

from sphinx.application import Sphinx
from sphinx.ext.autodoc import Options

from .formatting import format_both


logger = getLogger(__name__)
re_ret = re.compile("^:returns?: ")


def get_tuple_annot(annotation: type | None) -> tuple[type, ...] | None:
    from typing import Tuple, Union

    if annotation is None:
        return None
    origin = get_origin(annotation)
    if not origin:
        return None
    if origin is Union:
        for annotation in get_args(annotation):
            origin = get_origin(annotation)
            if origin in (tuple, Tuple):
                break
        else:
            return None
    return get_args(annotation)


def process_docstring(
    app: Sphinx,
    what: str,
    name: str,
    obj: Any,
    options: Options | None,
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
    except (AttributeError, TypeError):
        # Introspecting a slot wrapper will raise TypeError
        return
    ret_types = get_tuple_annot(hints.get("return"))
    if ret_types is None:
        return

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
        return

    # Meat
    idxs_ret_names = []
    for l, line in enumerate([l[i_prefix:] for l in lines[l_start : l_end + 1]]):
        if line.isidentifier() and lines[l + l_start + 1].startswith("    "):
            idxs_ret_names.append(l + l_start)

    if len(idxs_ret_names) == len(ret_types):
        for l, rt in zip(idxs_ret_names, ret_types):
            typ = format_both(rt, app.config)
            lines[l : l + 1] = [f"{lines[l]} : {typ}"]

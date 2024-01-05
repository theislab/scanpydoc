from __future__ import annotations

import re
import sys
import inspect
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin, get_type_hints
from typing import Tuple as t_Tuple  # noqa: UP035
from logging import getLogger

from sphinx_autodoc_typehints import format_annotation


if TYPE_CHECKING:
    from collections.abc import Sequence

    from sphinx.application import Sphinx
    from sphinx.ext.autodoc import Options


if sys.version_info > (3, 10):
    from types import UnionType

    UNION_TYPES = {Union, UnionType}
else:  # pragma: no cover
    UNION_TYPES = {Union}


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
            lines[l : l + 1] = [f"{lines[l]} : {typ}"]


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
        if line.isidentifier() and lines[l + l_start + 1].startswith("    "):
            idxs_ret_names.append(l + l_start)
    return idxs_ret_names

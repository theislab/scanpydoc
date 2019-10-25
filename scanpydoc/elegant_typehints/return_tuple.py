import inspect
import re
from typing import get_type_hints, Any, Union, Optional, Type, Tuple, List

from sphinx.application import Sphinx
from sphinx.ext.autodoc import Options

from .formatting import format_both


re_ret = re.compile("^:returns?: ")


def get_tuple_annot(annotation: Optional[Type]) -> Optional[Tuple[Type, ...]]:
    if annotation is None:
        return None
    origin = getattr(annotation, "__origin__", None)
    if not origin:
        return None
    if origin is Union:
        for annotation in annotation.__args__:
            origin = getattr(annotation, "__origin__", None)
            if origin in (tuple, Tuple):
                break
        else:
            return None
    return annotation.__args__


def process_docstring(
    app: Sphinx,
    what: str,
    name: str,
    obj: Any,
    options: Optional[Options],
    lines: List[str],
) -> None:
    # Handle complex objects
    if isinstance(obj, property):
        obj = obj.fget
    if not callable(obj):
        return
    if what in ("class", "exception"):
        obj = obj.__init__
    obj = inspect.unwrap(obj)
    ret_types = get_tuple_annot(get_type_hints(obj).get("return"))
    if ret_types is None:
        return

    # Get return section
    i_prefix = None
    l_start = None
    l_end = None
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
            typ = format_both(rt, app.config.typehints_fully_qualified)
            lines[l : l + 1] = [f"{lines[l]} : {typ}"]


# def process_signature(
#     app: Sphinx,
#     what: str,
#     name: str,
#     obj: Any,
#     options: Options,
#     signature: Optional[str],
#     return_annotation: str,
# ) -> Optional[Tuple[Optional[str], Optional[str]]]:
#     return signature, return_annotation

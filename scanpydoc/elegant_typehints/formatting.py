import inspect
from collections import abc
from typing import Any, Union  # Meta
from typing import Type, Mapping, Sequence, Iterable  # ABC
from typing import Dict, List, Tuple  # Concrete

from scanpydoc import elegant_typehints

try:
    from typing import Literal
except ImportError:
    try:
        from typing_extensions import Literal
    except ImportError:
        Literal = object()

import sphinx_autodoc_typehints
from sphinx_autodoc_typehints import format_annotation as _format_orig
from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst.roles import set_classes
from docutils.parsers.rst.states import Inliner, Struct
from docutils.utils import SystemMessage, unescape


def _format_full(annotation: Type[Any], fully_qualified: bool = False):
    if inspect.isclass(annotation) and annotation.__module__ == "builtins":
        return _format_orig(annotation, fully_qualified)

    origin = getattr(annotation, "__origin__", None)
    tilde = "" if fully_qualified else "~"

    annotation_cls = annotation if inspect.isclass(annotation) else type(annotation)
    if annotation_cls.__module__ == "typing":
        return _format_orig(annotation, fully_qualified)

    # Only if this is a real class we override sphinx_autodoc_typehints
    if inspect.isclass(annotation) or inspect.isclass(origin):
        full_name = f"{annotation.__module__}.{annotation.__qualname__}"
        override = elegant_typehints.qualname_overrides.get(full_name)
        role = "exc" if issubclass(annotation_cls, BaseException) else "class"
        if override is not None:
            return f":py:{role}:`{tilde}{override}`"

    return _format_orig(annotation, fully_qualified)


def _format_terse(annotation: Type[Any], fully_qualified: bool = False) -> str:
    origin = getattr(annotation, "__origin__", None)

    union_params = getattr(annotation, "__union_params__", None)
    # display `Union[A, B]` as `A, B`
    if origin is Union or union_params:
        params = union_params or getattr(annotation, "__args__", None)
        # Never use the `Optional` keyword in the displayed docs.
        # Use the more verbose `, None` instead,
        # as is the convention in the other large numerical packages
        # if len(params or []) == 2 and getattr(params[1], '__qualname__', None) == 'NoneType':
        #     return fa_orig(annotation)  # Optional[...]
        return ", ".join(_format_terse(p, fully_qualified) for p in params)

    # do not show the arguments of Mapping
    if origin in (abc.Mapping, Mapping):
        return f":py:class:`{'' if fully_qualified else '~'}typing.Mapping`"

    # display dict as {k: v}
    if origin in (dict, Dict):
        k, v = annotation.__args__
        return f"{{{_format_terse(k, fully_qualified)}: {_format_terse(v, fully_qualified)}}}"

    if origin is Literal or hasattr(annotation, "__values__"):
        values = getattr(annotation, "__args__", ()) or annotation.__values__
        return f"{{{', '.join(map(repr, values))}}}"

    return _format_full(annotation, fully_qualified)


def format_annotation(annotation: Type[Any], fully_qualified: bool = False) -> str:
    r"""Generate reStructuredText containing links to the types.

    Unlike :func:`sphinx_autodoc_typehints.format_annotation`,
    it tries to achieve a simpler style as seen in numeric packages like numpy.

    Args:
        annotation: A type or class used as type annotation.
        fully_qualified: If links should be formatted as fully qualified
            (e.g. ``:py:class:`foo.Bar```) or not (e.g. ``:py:class:`~foo.Bar```).

    Returns:
        reStructuredText describing the type
    """
    if sphinx_autodoc_typehints.format_annotation is not format_annotation:
        raise RuntimeError(
            "This function is not guaranteed to work correctly without overriding"
            "`sphinx_autodoc_typehints.format_annotation` with it."
        )

    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    if calframe[1][3] == "process_docstring":
        annot_fmt = format_both(annotation, fully_qualified)
        if elegant_typehints.annotate_defaults:
            variables = calframe[1].frame.f_locals
            sig = inspect.signature(variables["obj"])
            if variables["argname"] != "return":
                default = sig.parameters[variables["argname"]].default
                if default is not inspect.Parameter.empty:
                    annot_fmt += f" (default: ``{_escape(repr(default))}``)"
        return annot_fmt
    else:  # recursive use
        return _format_full(annotation, fully_qualified)


def format_both(annotation: Type[Any], fully_qualified: bool = False):
    return (
        f":annotation-terse:`{_escape(_format_terse(annotation, fully_qualified))}`\\ "
        f":annotation-full:`{_escape(_format_full(annotation, fully_qualified))}`"
    )


def _role_annot(
    name: str,
    rawtext: str,
    text: str,
    lineno: int,
    inliner: Inliner,
    options: Dict[str, Any] = {},
    content: Sequence[str] = (),
    # *,  # https://github.com/ambv/black/issues/613
    additional_classes: Iterable[str] = (),
) -> Tuple[List[Node], List[SystemMessage]]:
    options = options.copy()
    set_classes(options)
    if additional_classes:
        options["classes"] = options.get("classes", []).copy()
        options["classes"].extend(additional_classes)
    memo = Struct(
        document=inliner.document, reporter=inliner.reporter, language=inliner.language
    )
    node = nodes.inline(unescape(rawtext), "", **options)
    children, messages = inliner.parse(_unescape(text), lineno, memo, node)
    node.extend(children)
    return [node], messages


def _escape(rst: str) -> str:
    return rst.replace("`", "\\`")


def _unescape(rst: str) -> str:
    # TODO: IDK why the [ part is necessary.
    return unescape(rst).replace("\\`", "`").replace("[", "\\[")

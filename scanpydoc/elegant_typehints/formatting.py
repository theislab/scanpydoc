import inspect
import collections.abc as cabc
from functools import partial
from typing import Any, Union  # Meta
from typing import Type, Sequence, Iterable  # ABC
from typing import Dict, List, Tuple  # Concrete

try:  # 3.8 additions
    from typing import Literal, get_args, get_origin
except ImportError:
    from typing_extensions import Literal, get_args, get_origin

import sphinx_autodoc_typehints
from sphinx_autodoc_typehints import format_annotation as _format_orig
from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst.roles import set_classes
from docutils.parsers.rst.states import Inliner, Struct
from docutils.utils import SystemMessage, unescape

from scanpydoc import elegant_typehints


def _format_full(
    annotation: Type[Any],
    fully_qualified: bool = False,
    simplify_optional_unions: bool = True,
):
    if inspect.isclass(annotation) and annotation.__module__ == "builtins":
        return _format_orig(annotation, fully_qualified, simplify_optional_unions)

    origin = get_origin(annotation)
    tilde = "" if fully_qualified else "~"

    annotation_cls = annotation if inspect.isclass(annotation) else type(annotation)
    if annotation_cls.__module__ == "typing":
        return _format_orig(annotation, fully_qualified, simplify_optional_unions)

    # Only if this is a real class we override sphinx_autodoc_typehints
    if inspect.isclass(annotation) or inspect.isclass(origin):
        full_name = f"{annotation.__module__}.{annotation.__qualname__}"
        override = elegant_typehints.qualname_overrides.get(full_name)
        role = "exc" if issubclass(annotation_cls, BaseException) else "class"
        if override is not None:
            return f":py:{role}:`{tilde}{override}`"

    return _format_orig(annotation, fully_qualified, simplify_optional_unions)


def _format_terse(
    annotation: Type[Any],
    fully_qualified: bool = False,
    simplify_optional_unions: bool = True,
) -> str:
    origin = get_origin(annotation)
    args = get_args(annotation)
    tilde = "" if fully_qualified else "~"
    fmt = partial(
        _format_terse,
        fully_qualified=fully_qualified,
        simplify_optional_unions=simplify_optional_unions,
    )

    # display `Union[A, B]` as `A | B`
    if origin is Union:
        # Never use the `Optional` keyword in the displayed docs.
        # Use `| None` instead, similar to other large numerical packages.
        return " | ".join(map(fmt, args))

    # do not show the arguments of Mapping
    if origin is cabc.Mapping:
        return f":py:class:`{tilde}typing.Mapping`"

    # display dict as {k: v}
    if origin is dict:
        k, v = get_args(annotation)
        return f"{{{fmt(k)}: {fmt(v)}}}"

    # display Callable[[a1, a2], r] as (a1, a2) -> r
    if origin is cabc.Callable and len(args) == 2:
        params, ret = args
        params = ["…"] if params is Ellipsis else map(fmt, params)
        return f"({', '.join(params)}) → {fmt(ret)}"

    # display Literal as {'a', 'b', ...}
    if origin is Literal:
        return f"{{{', '.join(map(repr, args))}}}"

    return _format_full(annotation, fully_qualified, simplify_optional_unions)


def format_annotation(
    annotation: Type[Any],
    fully_qualified: bool = False,
    simplify_optional_unions: bool = True,
) -> str:
    r"""Generate reStructuredText containing links to the types.

    Unlike :func:`sphinx_autodoc_typehints.format_annotation`,
    it tries to achieve a simpler style as seen in numeric packages like numpy.

    Args:
        annotation: A type or class used as type annotation.
        fully_qualified: If links should be formatted as fully qualified
            (e.g. ``:py:class:`foo.Bar```) or not (e.g. ``:py:class:`~foo.Bar```).
        simplify_optional_unions: If Unions should be minimized if they contain
            3 or more elements one of which is ``None``. (If ``True``, e.g.
            ``Optional[Union[str, int]]`` becomes ``Union[str, int, None]``)

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
        annot_fmt = format_both(annotation, fully_qualified, simplify_optional_unions)
        if elegant_typehints.annotate_defaults:
            variables = calframe[1].frame.f_locals
            sig = inspect.signature(variables["obj"])
            arg_name = variables["argname"].replace(r"\_", "_")
            if arg_name != "return":
                default = sig.parameters[arg_name].default
                if default is not inspect.Parameter.empty:
                    annot_fmt += f" (default: ``{_escape(repr(default))}``)"
        return annot_fmt
    else:  # recursive use
        return _format_full(annotation, fully_qualified, simplify_optional_unions)


def format_both(
    annotation: Type[Any],
    fully_qualified: bool = False,
    simplify_optional_unions: bool = True,
) -> str:
    terse = _format_terse(annotation, fully_qualified, simplify_optional_unions)
    full = _format_full(annotation, fully_qualified, simplify_optional_unions)
    return f":annotation-terse:`{_escape(terse)}`\\ :annotation-full:`{_escape(full)}`"


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

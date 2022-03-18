import collections.abc as cabc
import inspect
from functools import partial
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Type, Union

from sphinx.config import Config


try:  # 3.8 additions
    from typing import Literal, get_args, get_origin
except ImportError:
    from typing_extensions import Literal, get_args, get_origin

from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst.roles import set_classes
from docutils.parsers.rst.states import Inliner, Struct
from docutils.utils import SystemMessage, unescape
from sphinx_autodoc_typehints import format_annotation as _format_orig

from scanpydoc import elegant_typehints


def _format_full(annotation: Type[Any], config: Config) -> Optional[str]:
    if inspect.isclass(annotation) and annotation.__module__ == "builtins":
        return None

    origin = get_origin(annotation)
    tilde = "" if config.typehints_fully_qualified else "~"

    annotation_cls = annotation if inspect.isclass(annotation) else type(annotation)
    if annotation_cls.__module__ == "typing":
        return None

    # Only if this is a real class we override sphinx_autodoc_typehints
    if inspect.isclass(annotation) or inspect.isclass(origin):
        full_name = f"{annotation.__module__}.{annotation.__qualname__}"
        override = elegant_typehints.qualname_overrides.get(full_name)
        role = "exc" if issubclass(annotation_cls, BaseException) else "class"
        if override is not None:
            return f":py:{role}:`{tilde}{override}`"

    return None


def _format_terse(annotation: Type[Any], config: Config) -> str:
    origin = get_origin(annotation)
    args = get_args(annotation)
    tilde = "" if config.typehints_fully_qualified else "~"
    fmt = partial(_format_terse, config=config)

    # display `Union[A, B]` as `A | B`
    if origin is Union:
        # Never use the `Optional` keyword in the displayed docs.
        # Use `| None` instead, similar to other large numerical packages.
        return " | ".join(map(fmt, args))

    # do not show the arguments of Mapping
    if origin is cabc.Mapping:
        return f":py:class:`{tilde}typing.Mapping`"

    # display dict as {k: v}
    if origin is dict and len(args) == 2:
        k, v = args
        return f"{{{fmt(k)}: {fmt(v)}}}"

    # display Callable[[a1, a2], r] as (a1, a2) -> r
    if origin is cabc.Callable and len(args) == 2:
        params, ret = args
        params = ["…"] if params is Ellipsis else map(fmt, params)
        return f"({', '.join(params)}) → {fmt(ret)}"

    # display Literal as {'a', 'b', ...}
    if origin is Literal:
        return f"{{{', '.join(map(repr, args))}}}"

    return _format_full(annotation, config) or _format_orig(annotation, config)


def format_annotation(annotation: Type[Any], config: Config) -> Optional[str]:
    r"""Generate reStructuredText containing links to the types.

    Unlike :func:`sphinx_autodoc_typehints.format_annotation`,
    it tries to achieve a simpler style as seen in numeric packages like numpy.

    Args:
        annotation: A type or class used as type annotation.
        config: Sphinx config containing ``sphinx-autodoc-typehints``’s options.

    Returns:
        reStructuredText describing the type
    """

    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    if calframe[2].function == "process_docstring" or (
        calframe[2].function == "_inject_types_to_docstring"
        and calframe[3].function == "process_docstring"
    ):
        return format_both(annotation, config)
    else:  # recursive use
        return _format_full(annotation, config)


def format_both(annotation: Type[Any], config: Config) -> str:
    terse = _format_terse(annotation, config)
    full = _format_full(annotation, config) or _format_orig(annotation, config)
    if terse == full:
        return terse
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

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, get_origin


try:
    from types import UnionType
except ImportError:
    UnionType = None

from docutils import nodes
from docutils.parsers.rst.roles import set_classes
from docutils.parsers.rst.states import Inliner, Struct
from docutils.utils import SystemMessage, unescape

from scanpydoc import elegant_typehints


if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from docutils.nodes import Node
    from sphinx.config import Config


def typehints_formatter(annotation: type[Any], config: Config) -> str | None:
    """Generate reStructuredText containing links to the types.

    Can be used as ``typehints_formatter`` for :mod:`sphinx_autodoc_typehints`,
    to respect the ``qualname_overrides`` option.

    Args:
        annotation: A type or class used as type annotation.
        config: Sphinx config containing ``sphinx-autodoc-typehints``’s options.

    Returns:
        reStructuredText describing the type
    """
    if inspect.isclass(annotation) and annotation.__module__ == "builtins":
        return None

    origin = get_origin(annotation)
    tilde = "" if config.typehints_fully_qualified else "~"

    annotation_cls = annotation if inspect.isclass(annotation) else type(annotation)
    if annotation_cls.__module__ == "typing":
        return None

    # Only if this is a real class we override sphinx_autodoc_typehints
    if inspect.isclass(annotation) or inspect.isclass(origin):
        try:
            full_name = f"{annotation.__module__}.{annotation.__qualname__}"
        except AttributeError:
            full_name = f"{origin.__module__}.{origin.__qualname__}"
        override = elegant_typehints.qualname_overrides.get(full_name)
        role = "exc" if issubclass(annotation_cls, BaseException) else "class"
        if override is not None:
            return f":py:{role}:`{tilde}{override}`"

    return None


def _role_annot(  # noqa: PLR0913
    name: str,  # noqa: ARG001
    rawtext: str,
    text: str,
    lineno: int,
    inliner: Inliner,
    options: dict[str, Any] | None = None,
    content: Sequence[str] = (),  # noqa: ARG001
    *,
    additional_classes: Iterable[str] = (),
) -> tuple[list[Node], list[SystemMessage]]:
    if options is None:
        options = {}
    options = options.copy()
    set_classes(options)
    if additional_classes:
        options["classes"] = options.get("classes", []).copy()
        options["classes"].extend(additional_classes)
    memo = Struct(
        document=inliner.document,
        reporter=inliner.reporter,
        language=inliner.language,
    )
    node = nodes.inline(unescape(rawtext), "", **options)
    children, messages = inliner.parse(_unescape(text), lineno, memo, node)
    node.extend(children)
    return [node], messages


def _unescape(rst: str) -> str:
    # IDK why the [ part is necessary.
    return unescape(rst).replace("\\`", "`").replace("[", "\\[")

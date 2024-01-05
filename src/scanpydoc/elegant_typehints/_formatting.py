from __future__ import annotations

import sys
import inspect
from typing import TYPE_CHECKING, Any, cast, get_origin


if sys.version_info >= (3, 10):
    from types import UnionType
else:  # pragma: no cover
    UnionType = None

from docutils.utils import unescape

from scanpydoc import elegant_typehints


if TYPE_CHECKING:
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
            if origin is not None:
                full_name = f"{origin.__module__}.{origin.__qualname__}"
            else:
                return None
        override = elegant_typehints.qualname_overrides.get(full_name)
        role = "exc" if issubclass(annotation_cls, BaseException) else "class"
        if override is not None:
            return f":py:{role}:`{tilde}{override}`"

    return None


def _unescape(rst: str) -> str:
    # IDK why the [ part is necessary.
    return cast(str, unescape(rst)).replace("\\`", "`").replace("[", "\\[")

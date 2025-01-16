from __future__ import annotations

import inspect
from types import GenericAlias
from typing import TYPE_CHECKING, Any, cast, get_args, get_origin

from sphinx_autodoc_typehints import format_annotation

from scanpydoc import elegant_typehints
from scanpydoc._types import _GenericAlias


if TYPE_CHECKING:
    from sphinx.config import Config


def typehints_formatter(annotation: type[Any], config: Config) -> str | None:
    """Generate reStructuredText containing links to the types.

    Can be used as ``typehints_formatter`` for :mod:`sphinx_autodoc_typehints`,
    to respect the ``qualname_overrides`` option.

    Arguments
    ---------
    annotation
        A type or class used as type annotation.
    config
        Sphinx config containing ``sphinx-autodoc-typehints``’s options.

    Returns
    -------
    reStructuredText describing the type
    """
    if inspect.isclass(annotation) and annotation.__module__ == "builtins":
        return None

    tilde = "" if config.typehints_fully_qualified else "~"

    if isinstance(annotation, GenericAlias | _GenericAlias):
        args = get_args(annotation)
        annotation = cast(type[Any], get_origin(annotation))
    else:
        args = None
    annotation_cls = annotation if inspect.isclass(annotation) else type(annotation)
    if annotation_cls.__module__ in {"typing", "types"}:
        return None

    # Only if this is a real class we override sphinx_autodoc_typehints
    if inspect.isclass(annotation):
        full_name = f"{annotation.__module__}.{annotation.__qualname__}"
        override = elegant_typehints.qualname_overrides.get((None, full_name))
        if override is not None:
            if args is None:
                formatted_args = ""
            else:
                formatted_args = ", ".join(
                    format_annotation(arg, config) for arg in args
                )
                formatted_args = rf"\ \[{formatted_args}]"
            role, qualname = override
            if role is None:
                role = (
                    "py:exc"
                    if issubclass(annotation_cls, BaseException)
                    else "py:class"
                )
            return f":{role}:`{tilde}{qualname}`{formatted_args}"

    return None

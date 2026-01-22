from __future__ import annotations

from types import GenericAlias
from typing import TYPE_CHECKING, TypeAliasType, cast, get_args, get_origin

from sphinx_autodoc_typehints import format_annotation

from scanpydoc import elegant_typehints
from scanpydoc._types import _GenericAlias


if TYPE_CHECKING:
    from typing import Any
    from collections.abc import Sequence

    from sphinx.config import Config


def typehints_formatter(annotation: object, config: Config) -> str | None:
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
    if isinstance(annotation, TypeAliasType):
        return format_annotation(annotation.__value__, config)

    if isinstance(annotation, type) and annotation.__module__ == "builtins":
        return None

    if isinstance(annotation, GenericAlias | _GenericAlias):
        args = get_args(annotation)
        annotation = cast("type", get_origin(annotation))
    else:
        args = None
    annotation_cls = annotation if isinstance(annotation, type) else type(annotation)
    if annotation_cls.__module__ in {"typing", "types"}:
        return None

    if isinstance(annotation, type):
        return _fmt_type(annotation, args, config)

    return None  # pragma: no cover


def _fmt_type(cls: type, args: Sequence[Any] | None, config: Config) -> str | None:
    full_name = f"{cls.__module__}.{cls.__qualname__}"
    if (
        override := elegant_typehints.qualname_overrides.get((None, full_name))
    ) is None:
        return None

    role, qualname = override
    if role == "doc":
        label = full_name if config.typehints_fully_qualified else cls.__qualname__
        return f":{role}:`{label} <{qualname}>`"

    tilde = "" if config.typehints_fully_qualified else "~"
    if role is None:
        role = "py:exc" if issubclass(cls, BaseException) else "py:class"
    if args is None:
        formatted_args = ""
    else:
        formatted_args = ", ".join(format_annotation(arg, config) for arg in args)
        formatted_args = rf"\ \[{formatted_args}]"
    return f":{role}:`{tilde}{qualname}`{formatted_args}"

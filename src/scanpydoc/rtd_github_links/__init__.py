"""GitHub URLs for class and method pages.

This extension does two things:

#. It registers a :ref:`Jinja filter <jinja:filters>` called :func:`github_url`
   that you can use to convert a module path into a GitHub URL.
#. It configures :mod:`sphinx.ext.linkcode` for you if loaded after it in ``conf.py``:

   .. code:: python

      extensions = [
          "scanpydoc",
          "sphinx.ext.linkcode",
      ]

      # no need to define `linkcode_resolve`

Configuration
-------------

Uses the following config values in ``conf.py``::

    rtd_links_prefix: os.PathLike | str = ...  # default: '.'

    # sphinx book theme style
    html_theme_options = dict(
        repository_url=...,
        repository_branch=...,
    )
    # or RTD theme style:
    html_context = dict(
        github_user=...,
        github_repo=...,
        github_version=...,
    )

The ``rtd_links_prefix`` is for figuring out the .py file path relative to the git root,
that is to construct the path in the GitHub URL.

Which html configuration style you want to use depends on your theme, e.g.
:doc:`Sphinx Book Theme <sphinx_book_theme:index>`.

``:github_url:`` usage
----------------------

You can use the filter e.g. in `autosummary templates`_.
To configure the :doc:`Sphinx Book Theme <sphinx_book_theme:index>`,
override the ``autosummary/base.rst`` template like this:

.. code:: restructuredtext

    :github_url: {{ fullname | github_url }}

    {% extends "!autosummary/base.rst" %}

.. _autosummary templates: \
   http://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html#customizing-templates
"""
from __future__ import annotations

import sys
import inspect
from types import ModuleType
from typing import TYPE_CHECKING
from pathlib import Path, PurePosixPath
from importlib import import_module
from dataclasses import fields, is_dataclass

from jinja2.defaults import DEFAULT_FILTERS  # type: ignore[attr-defined]

from scanpydoc import metadata, _setup_sig


if TYPE_CHECKING:
    from types import CodeType, FrameType, MethodType, FunctionType, TracebackType
    from typing import Any, TypeAlias
    from collections.abc import Callable

    _SourceObjectType: TypeAlias = (
        ModuleType
        | type[Any]
        | MethodType
        | FunctionType
        | TracebackType
        | FrameType
        | CodeType
        | Callable[..., Any]
    )

    from sphinx.config import Config
    from sphinx.application import Sphinx


rtd_links_prefix: PurePosixPath | None = None
github_base_url: str | None = None


def _init_vars(_app: Sphinx, config: Config) -> None:  # pragma: no cover
    """Run hook when ``conf.py`` has been loaded."""
    global github_base_url, rtd_links_prefix
    github_base_url, rtd_links_prefix = _infer_vars(config)


def _infer_vars(config: Config) -> tuple[str, PurePosixPath]:
    _check_html_config(config)
    try:
        github_base_url = "https://github.com/{github_user}/{github_repo}/tree/{github_version}".format_map(
            config.html_context,
        )
    except (AttributeError, KeyError):
        github_base_url = "{repository_url}/tree/{repository_branch}".format_map(
            config.html_theme_options,
        )
    rtd_links_prefix = PurePosixPath(config.rtd_links_prefix)
    return github_base_url, rtd_links_prefix


def _get_annotations(obj: _SourceObjectType) -> dict[str, Any]:
    if sys.version_info > (3, 10):
        from inspect import get_annotations
    else:  # pragma: no cover
        from get_annotations import get_annotations

    try:
        return get_annotations(obj)  # type: ignore[no-any-return,arg-type,unused-ignore]
    except TypeError:  # pragma: no cover
        return {}


def _get_obj_module(qualname: str) -> tuple[Any, ModuleType]:  # noqa: PLR0912
    """Get a module/class/attribute and its original module by qualname.

    Returns `None` as `obj` if it’s an annotated field without value.
    """
    modname = qualname
    attr_path: list[str] = []
    while "." in modname and modname not in sys.modules:
        modname, leaf = modname.rsplit(".", 1)
        attr_path.insert(0, leaf)

    # retrieve object and find original module name
    mod = sys.modules[modname]
    obj = None if attr_path else mod
    del modname
    for attr_name in attr_path:
        try:
            thing = getattr(mod if obj is None else obj, attr_name)
        except AttributeError as e:
            if is_dataclass(obj):
                thing = next(f for f in fields(obj) if f.name == attr_name)
            elif obj is not None and attr_name in _get_annotations(obj):
                thing = None
            else:  # pragma: no cover
                try:
                    thing = import_module(f"{mod.__name__}.{attr_name}")
                except ImportError:
                    raise e from None
        if isinstance(thing, ModuleType):  # pragma: no cover
            mod = thing
        elif is_dataclass(obj):
            obj = thing
        else:
            obj = thing
            mod_orig = getattr(obj, "__module__", None)
            if mod_orig is not None:
                mod = sys.modules[mod_orig]

    return obj, mod


def _get_linenos(obj: _SourceObjectType) -> tuple[int, int] | tuple[None, None]:
    """Get an object’s line numbers."""
    try:
        lines, start = inspect.getsourcelines(obj)
    except TypeError:
        return None, None
    else:
        return start, start + len(lines) - 1


def _module_path(obj: _SourceObjectType, module: ModuleType) -> PurePosixPath:
    """Relative module path to parent directory of toplevel module."""
    while hasattr(obj, "__wrapped__"):
        obj = obj.__wrapped__
    try:
        file = Path(inspect.getabsfile(obj))
    except TypeError:
        file = Path(module.__file__ or "")
    offset = -1 if file.name == "__init__.py" else 0
    parts = module.__name__.split(".")
    return PurePosixPath(*file.parts[offset - len(parts) :])


def github_url(qualname: str) -> str:
    """Get the full GitHub URL for some object’s qualname.

    Parameters
    ----------
    qualname
        The full qualified name of a function, class, method or module

    Returns
    -------
    A GitHub URL derived from the :confval:`html_context`
    or the :confval:`html_theme_options`.
    """
    try:
        obj, module = _get_obj_module(qualname)
    except Exception as e:
        if sys.version_info >= (3, 11):
            e.add_note(f"Qualname: {qualname!r}")
        raise
    assert rtd_links_prefix is not None  # noqa: S101
    path = rtd_links_prefix / _module_path(obj, module)
    start, end = _get_linenos(obj)
    fragment = f"#L{start}-L{end}" if start and end else ""
    return f"{github_base_url}/{path}{fragment}"


def _check_html_config(config: Config) -> None:
    options = dict(
        html_context={"github_user", "github_repo", "github_version"},
        html_theme_options={"repository_url", "repository_branch"},
    )
    if not any(name in config for name in options):
        msg = (
            f"Extension {__name__} needs “html_context” "
            "or “html_theme_options” to be defined in conf.py"
        )
        raise ValueError(msg)
    missing_value_sets = {
        name: opts - getattr(config, name, {}).keys() for name, opts in options.items()
    }
    if not all(missing_value_sets.values()):
        return  # a valid configuration was found

    mvs = " or ".join(
        f"{name} {', '.join(repr(mv) for mv in mvs)}"
        for name, mvs in missing_value_sets.items()
    )
    msg = f"Extension {__name__} needs {mvs} to be defined in conf.py."
    for name in options:
        if name in config:
            msg += f"\n{name} = {config[name]!r}"
    raise ValueError(msg)


@_setup_sig
def setup(app: Sphinx) -> dict[str, Any]:
    """Register the :func:`github_url` :ref:`Jinja filter <jinja:filters>`."""
    app.add_config_value("rtd_links_prefix", PurePosixPath("."), "")
    app.connect("config-inited", _init_vars)

    # if linkcode config not set
    if "linkcode_resolve" not in app.config or app.config["linkcode_resolve"] is None:
        from ._linkcode import linkcode_resolve

        app.config["linkcode_resolve"] = linkcode_resolve

    # html_context doesn’t apply to autosummary templates ☹
    # and there’s no way to insert filters into those templates
    # so we have to modify the default filters
    DEFAULT_FILTERS["github_url"] = github_url

    return metadata

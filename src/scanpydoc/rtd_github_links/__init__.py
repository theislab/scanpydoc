"""GitHub URLs for class and method pages.

This extension does two things:

#. It registers a :ref:`Jinja filter <jinja:filters>` called :func:`github_url`
   that you can use to convert a module path into a GitHub URL.
#. It configures `sphinx.ext.linkcode` for you if loaded after it:

   .. code:: python

      import sys
      from pathlib import Path

      HERE = Path(__file__).parent
      # make sure modules are import from the right place
      sys.path.insert(0, HERE.parent / "src")

      extensions = [
          "scanpydoc",
          "sphinx.ext.linkcode",
      ]

      # no need to define `linkcode_resolve`

Configuration
-------------

Uses the following config values in ``conf.py``::

    project_dir: Path = ...  # default: Path.cwd()
    html_context = dict(
        repository_url=...,
        repository_branch=...,
    )

The ``project_dir`` is used to figure out the .py file path relative to the git root,
that is to construct the path in the github URL.

The ``html_context`` is e.g. also used like this in the
:doc:`Sphinx Book Theme <sphinx_book_theme:index>`.

Usage
-----

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

import inspect
import sys
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any

from jinja2.defaults import DEFAULT_FILTERS
from sphinx.application import Sphinx
from sphinx.config import Config

from .. import _setup_sig, metadata


project_dir = None  # type: Path
github_base_url = None  # type: str


def _init_vars(app: Sphinx, config: Config):
    """Called when ``conf.py`` has been loaded."""
    global github_base_url, project_dir
    _check_html_context(config)
    try:
        github_base_url = "https://github.com/{github_user}/{github_repo}/tree/{github_version}".format_map(
            config.html_context
        )
    except KeyError:
        github_base_url = "{repository_url}/tree/{repository_branch}".format_map(
            config.html_context
        )
    project_dir = Path(config.project_dir)


def _get_obj_module(qualname: str) -> tuple[Any, ModuleType]:
    """Get a module/class/attribute and its original module by qualname."""
    modname = qualname
    attr_path = []
    while modname not in sys.modules:
        modname, leaf = modname.rsplit(".", 1)
        attr_path.insert(0, leaf)

    # retrieve object and find original module name
    mod = sys.modules[modname]
    obj = None
    for attr_name in attr_path:
        try:
            thing = getattr(mod if obj is None else obj, attr_name)
        except AttributeError:
            if is_dataclass(obj):
                thing = next(f for f in fields(obj) if f.name == attr_name)
            else:
                raise
        if isinstance(thing, ModuleType):
            mod = thing
        else:
            obj = thing
            mod_orig = getattr(obj, "__module__", None)
            if mod_orig is not None:
                mod = sys.modules[mod_orig]

    return obj, mod


def _get_linenos(obj):
    """Get an object’s line numbers."""
    try:
        lines, start = inspect.getsourcelines(obj)
    except TypeError:
        return None, None
    else:
        return start, start + len(lines) - 1


def github_url(qualname: str) -> str:
    """Get the full GitHub URL for some object’s qualname.

    Args:
        qualname: The full qualified name of a function, class, method or module

    Returns:
        A GitHub URL derived from the :confval:`html_context`.
    """
    try:
        obj, module = _get_obj_module(qualname)
    except Exception:
        print(f"Error in github_url({qualname!r}):", file=sys.stderr)
        raise
    try:  # only works when installed in dev mode
        path = PurePosixPath(Path(module.__file__).resolve().relative_to(project_dir))
    except ValueError:
        # no dev mode or something from another package
        path = PurePosixPath(module.__file__.split("/")[-2:])
        if (project_dir / "src").is_dir():
            path = "src" / path
    start, end = _get_linenos(obj)
    fragment = f"#L{start}-L{end}" if start and end else ""
    return f"{github_base_url}/{path}{fragment}"


def _check_html_context(config: Config):
    try:
        html_context: dict[str, Any] = config.html_context
    except AttributeError:
        raise ValueError(
            f"Extension {__name__} needs “html_context” to be defined in conf.py"
        )
    options = [
        {"github_user", "github_repo", "github_version"},
        {"repository_url", "repository_branch"},
    ]
    missing_value_sets = [opt - html_context.keys() for opt in options]
    if all(missing_value_sets):
        mvs = " or ".join(
            ", ".join(repr(mv) for mv in mvs) for mvs in missing_value_sets
        )
        raise ValueError(
            f"Extension {__name__} needs html_context {mvs} to be defined in conf.py.\n"
            f"html_context = {html_context!r}"
        )


@_setup_sig
def setup(app: Sphinx) -> dict[str, Any]:
    """Register the :func:`github_url` :ref:`Jinja filter <jinja:filters>`."""
    # Guess default project dir
    proj_dir = Path.cwd()
    if proj_dir.name == "docs":
        proj_dir = proj_dir.parent
    elif not (proj_dir / "docs").is_dir():
        proj_dir = proj_dir.parent

    app.add_config_value("project_dir", proj_dir, "")
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


if True:  # test data
    from dataclasses import dataclass, field, fields, is_dataclass

    @dataclass
    class _TestCls:
        test_attr: dict[str, str] = field(default_factory=dict)

"""GitHub URLs for class and method pages

This extension registers a :ref:`Jinja filter <jinja:filters>` called :func:`github_url`
that you can use to convert a module path into a GitHub URL

Configuration
-------------

Uses the following config values in ``conf.py``::

    project_dir: Path = ...  # default: Path.cwd()
    html_context = dict(
        github_user=...,
        github_repo=...,
        github_version=...,
    )

The ``project_dir`` is used to figure out the .py file path relative to the git root,
that is to construct the path in the github URL.

The ``html_context`` is e.g. also used like this in the sphinx_rtd_theme_.

Usage
-----

You can use the filter e.g. in `autosummary templates`_.
To configure the sphinx_rtd_theme_, override the ``autosummary/base.rst`` template like this:

.. code:: restructuredtext

    :github_url: {{ fullname | github_url }}

    {% extends "!autosummary/base.rst" %}

.. _autosummary templates: http://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html#customizing-templates
.. _sphinx_rtd_theme: https://sphinx-rtd-theme.readthedocs.io/en/latest/
"""
import inspect
import sys
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Dict, Any, Tuple

from jinja2.defaults import DEFAULT_FILTERS
from sphinx.application import Sphinx
from sphinx.config import Config

from . import _setup_sig, metadata


project_dir = None  # type: Path
github_base_url = None  # type: str


def _init_vars(app: Sphinx, config: Config):
    """Called when ``conf.py`` has been loaded"""
    global github_base_url, project_dir
    _check_html_context(config)
    github_base_url = "https://github.com/{github_user}/{github_repo}/tree/{github_version}".format_map(
        config.html_context
    )
    project_dir = Path(config.project_dir)


def _get_obj_module(qualname: str) -> Tuple[Any, ModuleType]:
    """Get a module/class/attribute and its original module by qualname"""
    modname = qualname
    attr_path = []
    while modname not in sys.modules:
        modname, leaf = modname.rsplit(".", 1)
        attr_path.insert(0, leaf)

    # retrieve object and find original module name
    mod = sys.modules[modname]
    obj = None
    for attr_name in attr_path:
        thing = getattr(mod if obj is None else obj, attr_name)
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
    try:
        path = PurePosixPath(Path(module.__file__).resolve().relative_to(project_dir))
    except ValueError:
        # trying to document something from another package
        path = "/".join(module.__file__.split("/")[-2:])
    start, end = _get_linenos(obj)
    fragment = f"#L{start}-L{end}" if start and end else ""
    return f"{github_base_url}/{path}{fragment}"


def _check_html_context(config: Config):
    try:
        html_context = config.html_context
    except AttributeError:
        raise ValueError(
            f"Extension {__name__} needs “html_context” to be defined in conf.py"
        )
    missing_values = {
        "github_user",
        "github_repo",
        "github_version",
    } - html_context.keys()
    if missing_values:
        mvs = ", ".join([f"html_context[{mv!r}]" for mv in missing_values])
        raise ValueError(
            f"Extension {__name__} needs “{mvs}” to be defined in conf.py.\n"
            f"html_context = {html_context!r}"
        )


@_setup_sig
def setup(app: Sphinx) -> Dict[str, Any]:
    """Register the :func:`github_url` :ref:`Jinja filter <jinja:filters>`."""
    # Guess default project dir
    proj_dir = Path.cwd()
    if proj_dir.name == "docs":
        proj_dir = proj_dir.parent
    elif not (proj_dir / "docs").is_dir():
        proj_dir = proj_dir.parent

    app.add_config_value("project_dir", proj_dir, "")
    app.connect("config-inited", _init_vars)

    # html_context doesn’t apply to autosummary templates ☹
    # and there’s no way to insert filters into those templates
    # so we have to modify the default filters
    DEFAULT_FILTERS["github_url"] = github_url

    return metadata

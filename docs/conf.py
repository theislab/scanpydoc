"""Sphinx configuration."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from pathlib import PurePosixPath
from datetime import UTC, datetime
from importlib.metadata import metadata

from jinja2.tests import TESTS


if TYPE_CHECKING:
    from sphinx.application import Sphinx


extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",  # needs to be after napoleon
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "scanpydoc",
    "sphinx.ext.linkcode",  # needs to be after scanpydoc
]

intersphinx_mapping = dict(
    python=("https://docs.python.org/3", None),
    jinja=("https://jinja.palletsprojects.com/en/2.10.x/", None),
    docutils=("https://sphinx-docutils.readthedocs.io/en/latest/", None),
    sphinx=("https://www.sphinx-doc.org/en/master/", None),
    sphinx_book_theme=("https://sphinx-book-theme.readthedocs.io/en/stable/", None),
    # examples
    numpy=("https://numpy.org/doc/stable/", None),
    anndata=("https://anndata.readthedocs.io/en/latest/", None),
    pandas=("https://pandas.pydata.org/pandas-docs/stable/", None),
    scipy=("https://docs.scipy.org/doc/scipy/", None),
)

# general information
meta = metadata("scanpydoc")
project = meta["name"]
author = meta["author-email"].split(" <")[0]
copyright = f"{datetime.now(tz=UTC):%Y}, {author}."  # noqa: A001
version = release = meta["version"]

master_doc = "index"
templates_path = ["_templates"]

# Generate .rst stubs for modules using autosummary
autosummary_generate = True
autosummary_ignore_module_all = False
# Don’t add module paths to documented functions’ names
add_module_names = False

napoleon_google_docstring = False
napoleon_numpy_docstring = True


def test_search(value: str, pattern: str) -> bool:
    """Tests if `pattern` can be found in `value`."""
    return bool(re.search(pattern, value))


# IDK if there’s a good way to do this without modifying the global list
TESTS["search"] = test_search

html_theme = "scanpydoc"
html_theme_options = dict(
    repository_url="https://github.com/theislab/scanpydoc",
    repository_branch="main",
    use_repository_button=True,
)

rtd_links_prefix = PurePosixPath("src")

suppress_warnings = [
    # when documenting DLTypedField, s-a-t tries to get its .list_type’s typehints
    "sphinx_autodoc_typehints.guarded_import",
]


def setup(app: Sphinx) -> None:
    """Set up custom Sphinx extension."""
    app.add_object_type(
        "confval",
        "confval",
        objname="configuration value",
        indextemplate="pair: %s; configuration value",
    )

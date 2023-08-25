"""A series of Sphinx extensions to get maintainable numpydoc style documentation.

This module is also an extension itself which simply sets up all included extensions.
"""
from __future__ import annotations

from textwrap import indent
from typing import TYPE_CHECKING, Any

from ._version import __version__


if TYPE_CHECKING:
    from collections.abc import Callable

    from sphinx.application import Sphinx


metadata = dict(version=__version__, env_version=1, parallel_read_safe=True)

# Can’t seem to be able to do this in numpydoc style:
# https://github.com/sphinx-doc/sphinx/issues/5887
setup_sig_str = """\
Args:
    app: Sphinx app to set this :term:`sphinx:extension` up for

Returns:
    :ref:`Metadata <sphinx:ext-metadata>` for this extension.
"""


def _setup_sig(fn: Callable) -> Callable:
    fn.__doc__ += "\n\n" + indent(setup_sig_str, " " * 4)
    return fn


@_setup_sig
def setup(app: Sphinx) -> dict[str, Any]:
    """Set up all included extensions!."""
    app.setup_extension("scanpydoc.autosummary_generate_imported")
    app.setup_extension("scanpydoc.definition_list_typed_field")
    app.setup_extension("scanpydoc.elegant_typehints")
    app.setup_extension("scanpydoc.rtd_github_links")
    app.setup_extension("scanpydoc.theme")
    return metadata

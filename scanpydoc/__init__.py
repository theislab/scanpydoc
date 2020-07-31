"""A series of Sphinx extensions to get easy to maintain, numpydoc style documentation.

This module is also an extension itself which simply sets up all included extensions.
"""
from textwrap import indent
from typing import Any, Dict

from get_version import get_version
from sphinx.application import Sphinx


__version__ = get_version(__file__)

metadata = dict(version=__version__, env_version=1, parallel_read_safe=True)

# Can’t seem to be able to do this in numpydoc style:
# https://github.com/sphinx-doc/sphinx/issues/5887
setup_sig_str = """\
Args:
    app: Sphinx app to set this :term:`sphinx:extension` up for

Returns:
    :ref:`Metadata <sphinx:ext-metadata>` for this extension.
"""


def _setup_sig(fn):
    fn.__doc__ += "\n\n" + indent(setup_sig_str, " " * 4)
    return fn


@_setup_sig
def setup(app: Sphinx) -> Dict[str, Any]:
    """Set up all included extensions!"""
    app.setup_extension("scanpydoc.autosummary_generate_imported")
    app.setup_extension("scanpydoc.definition_list_typed_field")
    app.setup_extension("scanpydoc.elegant_typehints")
    app.setup_extension("scanpydoc.rtd_github_links")
    app.setup_extension("scanpydoc.theme")
    return metadata

"""A series of Sphinx extensions to get maintainable numpydoc style documentation.

This module is also an extension itself which simply sets up all included extensions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from textwrap import indent
from collections.abc import Callable

from sphinx.util import logging

from ._version import __version__


if TYPE_CHECKING:
    from sphinx.application import Sphinx


metadata = dict(version=__version__, env_version=1, parallel_read_safe=True)

_logger = logging.getLogger(__name__)
_setting_up_all = False


def _warn_deprecated(name: str, replacement: str) -> None:
    """Emit a Sphinx warning, so it counts toward the total and fails ``-W`` builds."""
    if _setting_up_all:  # `scanpydoc` itself already warned
        return
    _logger.warning(
        "The `%s` Sphinx extension is deprecated. "
        "Use %s from scverse-doc instead: https://github.com/scverse/scverse-doc",
        name,
        replacement,
        type="scanpydoc",
        subtype="deprecated",
    )


# Can’t seem to be able to do this in numpydoc style:
# https://github.com/sphinx-doc/sphinx/issues/5887
setup_sig_str = """\
Arguments
---------
app
    Sphinx app to set this :term:`sphinx:extension` up for

Returns
-------
:ref:`Metadata <sphinx:ext-metadata>` for this extension.
"""


def _setup_sig[C: Callable[..., Any]](fn: C) -> C:
    fn.__doc__ = f"{fn.__doc__ or ''}\n\n{indent(setup_sig_str, ' ' * 4)}"
    return fn


@_setup_sig
def setup(app: Sphinx) -> dict[str, Any]:
    """Set up all included extensions!"""  # noqa: D400
    global _setting_up_all  # noqa: PLW0603
    _warn_deprecated(__name__, '`extensions = ["scverse_doc"]`')
    _setting_up_all = True
    try:
        app.setup_extension("scanpydoc.definition_list_typed_field")
        app.setup_extension("scanpydoc.elegant_typehints")
        app.setup_extension("scanpydoc.rtd_github_links")
        app.setup_extension("scanpydoc.theme")
        app.setup_extension("scanpydoc.release_notes")
    finally:
        _setting_up_all = False
    return metadata

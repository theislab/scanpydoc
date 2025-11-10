"""Generate autosummary for imported members.

.. deprecated:: 0.11.0

   Use ``autosummary_imported_members = True`` instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import _setup_sig


if TYPE_CHECKING:
    from typing import Never

    from sphinx.application import Sphinx


@_setup_sig
def setup(_app: Sphinx) -> Never:  # pragma: no cover
    """Throws an :exc:`ImportError`."""
    msg = (
        "Please use `autosummary_imported_members = True` "
        f"instead of the {__name__} Sphinx extension."
    )
    raise ImportError(msg)

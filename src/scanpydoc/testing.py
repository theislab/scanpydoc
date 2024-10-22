"""Testing utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol


if TYPE_CHECKING:
    from typing import Any

    from sphinx.testing.util import SphinxTestApp


class MakeApp(Protocol):
    """Create a SphinxTestApp instance."""

    def __call__(  # noqa: D102
        self,
        builder: str = "html",
        /,
        *,
        exception_on_warning: bool = False,
        **conf: Any,  # noqa: ANN401
    ) -> SphinxTestApp: ...

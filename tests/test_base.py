"""Test things that aren’t sub-extension specific."""

from __future__ import annotations

import pkgutil
from functools import partial
from importlib import import_module
from typing import TYPE_CHECKING

import scanpydoc


if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest
    from sphinx.application import Sphinx


def test_all_get_installed(
    monkeypatch: pytest.MonkeyPatch,
    make_app_setup: Callable[..., Sphinx],
) -> None:
    setups_seen = set()
    setups_called = {}
    for _finder, mod_name, _ in pkgutil.walk_packages(
        scanpydoc.__path__,
        f"{scanpydoc.__name__}.",
    ):
        mod = import_module(mod_name)
        if not hasattr(mod, "setup"):
            continue
        setups_seen.add(mod_name)
        monkeypatch.setattr(mod, "setup", partial(setups_called.__setitem__, mod_name))

    app = make_app_setup()
    app.setup_extension("scanpydoc")

    assert setups_called.keys() == setups_seen
    for app2 in setups_called.values():
        assert app is app2

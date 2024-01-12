"""Test things that aren’t sub-extension specific."""

from __future__ import annotations

import pkgutil
from typing import TYPE_CHECKING
from functools import partial
from importlib import import_module

import scanpydoc


if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest
    from sphinx.application import Sphinx


DEPRECATED = frozenset({"scanpydoc.autosummary_generate_imported"})


def test_all_get_installed(
    monkeypatch: pytest.MonkeyPatch, make_app_setup: Callable[..., Sphinx]
) -> None:
    setups_seen: set[str] = set()
    setups_called: dict[str, Sphinx] = {}
    for _finder, mod_name, _ in pkgutil.walk_packages(
        scanpydoc.__path__, f"{scanpydoc.__name__}."
    ):
        mod = import_module(mod_name)
        if (
            mod_name in DEPRECATED
            or any(m.startswith("_") for m in mod_name.split("."))
            or not hasattr(mod, "setup")
        ):
            continue
        setups_seen.add(mod_name)
        monkeypatch.setattr(mod, "setup", partial(setups_called.__setitem__, mod_name))

    app = make_app_setup()
    app.setup_extension("scanpydoc")

    assert set(setups_called) == setups_seen
    for app2 in setups_called.values():
        assert app is app2

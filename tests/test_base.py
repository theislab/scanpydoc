"""Test things that aren’t sub-extension specific."""

from __future__ import annotations

import pkgutil
from typing import TYPE_CHECKING, cast
from functools import partial
from importlib import import_module

import pytest

import scanpydoc


if TYPE_CHECKING:
    from io import StringIO

    from sphinx.application import Sphinx

    from scanpydoc.testing import MakeApp


DEPRECATED = frozenset({"scanpydoc.autosummary_generate_imported"})


def test_all_get_installed(
    monkeypatch: pytest.MonkeyPatch, make_app_setup: MakeApp
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


@pytest.mark.parametrize(
    ("ext", "replacement"),
    [
        pytest.param("scanpydoc", '["scverse_doc"]', id="all"),
        pytest.param("scanpydoc.release_notes", "scverse_doc.release_notes", id="sub"),
    ],
)
def test_deprecation_warning(
    make_app_setup: MakeApp, ext: str, replacement: str
) -> None:
    app = make_app_setup()
    app.config.suppress_warnings = []  # conftest suppresses scanpydoc.deprecated
    app.setup_extension("sphinx.ext.autodoc")  # needed by elegant_typehints
    app.setup_extension(ext)
    msgs = [
        line
        for line in cast("StringIO", app._warning).getvalue().splitlines()  # noqa: SLF001
        if "deprecated" in line
    ]
    assert len(msgs) == 1, msgs  # setting up all only warns once
    assert f"`{ext}`" in msgs[0]
    assert replacement in msgs[0]

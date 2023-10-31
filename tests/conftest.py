"""Custom pytest fixtures and setup."""

from __future__ import annotations

import importlib.util
import linecache
import sys
from textwrap import dedent
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import pytest


if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from types import ModuleType

    from docutils.nodes import document
    from docutils.writers import Writer
    from sphinx.application import Sphinx


@pytest.fixture()
def make_app_setup(
    make_app: Callable[..., Sphinx],
    tmp_path: Path,
) -> Callable[..., Sphinx]:
    def make_app_setup(**conf: Any) -> Sphinx:  # noqa: ANN401
        (tmp_path / "conf.py").write_text("")
        return make_app(srcdir=tmp_path, confoverrides=conf)

    return make_app_setup


@pytest.fixture()
def render() -> Callable[[Sphinx, document], str]:
    def _render(app: Sphinx, doc: document) -> str:
        # Doesn’t work as desc is an Admonition and the HTML writer doesn’t handle it
        app.builder.prepare_writing({doc["source"]})
        writer: Writer = app.builder.docwriter
        writer.document = doc
        writer.document.settings = app.builder.docsettings
        writer.translate()
        return writer.output

    return _render


@pytest.fixture()
def make_module(tmp_path: Path) -> Callable[[str, str], ModuleType]:
    added_modules = []

    def make_module(name: str, code: str) -> ModuleType:
        code = dedent(code)
        assert name not in sys.modules
        spec = importlib.util.spec_from_loader(name, loader=None)
        mod = sys.modules[name] = importlib.util.module_from_spec(spec)
        path = tmp_path / f"{name}_{str(uuid4()).replace('-', '_')}.py"
        path.write_text(code)
        mod.__file__ = str(path)
        exec(code, mod.__dict__)  # noqa: S102
        linecache.updatecache(str(path), mod.__dict__)
        added_modules.append(name)
        return mod

    yield make_module

    for name in added_modules:
        del sys.modules[name]

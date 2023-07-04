from __future__ import annotations

import importlib.util
import linecache
import sys
from collections.abc import Callable
from textwrap import dedent
from uuid import uuid4

import pytest
from docutils.nodes import document
from sphinx.application import Sphinx
from sphinx.testing.path import path as STP


@pytest.fixture
def make_app_setup(make_app, tmp_path) -> Callable[..., Sphinx]:
    def make_app_setup(**conf) -> Sphinx:
        (tmp_path / "conf.py").write_text("")
        return make_app(srcdir=STP(tmp_path), confoverrides=conf)

    return make_app_setup


@pytest.fixture
def render() -> Callable[[Sphinx, document], str]:
    def _render(app: Sphinx, doc: document) -> str:
        # Doesn’t work as desc is an Admonition and the HTML writer doesn’t handle it
        # print(app.builder.render_partial(doc[1]))
        app.builder.prepare_writing({doc["source"]})
        writer = app.builder.docwriter  # type: Writer
        writer.document = doc
        writer.document.settings = app.builder.docsettings
        writer.translate()
        return writer.output

    return _render


@pytest.fixture
def make_module(tmp_path):
    added_modules = []

    def make_module(name, code):
        code = dedent(code)
        assert name not in sys.modules
        spec = importlib.util.spec_from_loader(name, loader=None)
        mod = sys.modules[name] = importlib.util.module_from_spec(spec)
        path = tmp_path / f"{name}_{str(uuid4()).replace('-', '_')}.py"
        path.write_text(code)
        mod.__file__ = str(path)
        exec(code, mod.__dict__)
        linecache.updatecache(str(path), mod.__dict__)
        added_modules.append(name)
        return mod

    yield make_module

    for name in added_modules:
        del sys.modules[name]

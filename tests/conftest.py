import importlib.util
import sys
import typing as t
from tempfile import NamedTemporaryFile
from textwrap import dedent

import pytest
from docutils.nodes import document
from docutils.writers import Writer
from sphinx.application import Sphinx
from sphinx.io import read_doc
from sphinx.testing.fixtures import make_app, test_params  # noqa
from sphinx.testing.path import path as STP
from sphinx.util import rst
from sphinx.util.docutils import sphinx_domains


@pytest.fixture
def make_app_setup(make_app, tmp_path) -> t.Callable[..., Sphinx]:
    def make_app_setup(**conf) -> Sphinx:
        (tmp_path / "conf.py").write_text("")
        return make_app(srcdir=STP(tmp_path), confoverrides=conf)

    return make_app_setup


@pytest.fixture
def parse() -> t.Callable[[Sphinx, str], document]:
    def _parse(app: Sphinx, code: str) -> document:
        with NamedTemporaryFile("w+", suffix=".rst", dir=app.env.srcdir) as f:
            f.write(code)
            f.flush()
            app.env.prepare_settings(f.name)
            with sphinx_domains(app.env), rst.default_role(
                f.name, app.config.default_role
            ):
                return read_doc(app, app.env, f.name)

    return _parse


@pytest.fixture
def render() -> t.Callable[[Sphinx, document], str]:
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
def make_module():
    added_modules = []

    def make_module(name, code):
        assert name not in sys.modules
        spec = importlib.util.spec_from_loader(name, loader=None)
        mod = sys.modules[name] = importlib.util.module_from_spec(spec)
        exec(dedent(code), mod.__dict__)
        added_modules.append(name)
        return mod

    yield make_module

    for name in added_modules:
        del sys.modules[name]

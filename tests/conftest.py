from tempfile import NamedTemporaryFile
from typing import Callable

import pytest
from docutils.nodes import document
from docutils.writers import Writer
from sphinx.application import Sphinx
from sphinx.io import read_doc
from sphinx.testing.fixtures import make_app, test_params
from sphinx.testing.path import path as STP
from sphinx.util import rst
from sphinx.util.docutils import sphinx_domains


@pytest.fixture
def app_no_setup(make_app, tmp_path) -> Sphinx:
    (tmp_path / "conf.py").write_text("")
    return make_app(srcdir=STP(tmp_path))


@pytest.fixture
def parse() -> Callable[[Sphinx, str], document]:
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

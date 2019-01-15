import pytest
from sphinx.application import Sphinx
from sphinx.testing.fixtures import make_app, test_params
from sphinx.testing.path import path as STP


@pytest.fixture
def app_no_setup(make_app, tmp_path) -> Sphinx:
    (tmp_path / "conf.py").write_text("")
    return make_app(srcdir=STP(tmp_path))

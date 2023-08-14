from dataclasses import Field
from importlib import import_module
from pathlib import Path, PurePosixPath

import pytest
from _pytest.monkeypatch import MonkeyPatch

from scanpydoc.rtd_github_links import _get_linenos, _get_obj_module, github_url


HERE = Path(__file__).parent


@pytest.fixture
def _env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("scanpydoc.rtd_github_links.github_base_url", "x")


@pytest.fixture(params=[".", "src"])
def prefix(monkeypatch: MonkeyPatch, _env, request) -> PurePosixPath:
    pfx = PurePosixPath(request.param)
    monkeypatch.setattr("scanpydoc.rtd_github_links.rtd_links_prefix", pfx)
    return "x" / pfx / "scanpydoc"


@pytest.mark.parametrize(
    ("module", "name", "obj_path"),
    [
        pytest.param(
            *("rtd_github_links", "github_url", "rtd_github_links/__init__.py"),
            id="basic",
        ),
        pytest.param(
            *("elegant_typehints", "example_func", "elegant_typehints/example.py"),
            id="reexport",
        ),
    ],
)
def test_as_function(prefix, module, name, obj_path):
    assert github_url(f"scanpydoc.{module}") == str(prefix / module / "__init__.py")
    obj = getattr(import_module(f"scanpydoc.{module}"), name)
    s, e = _get_linenos(obj)
    assert github_url(f"scanpydoc.{module}.{name}") == f"{prefix}/{obj_path}#L{s}-L{e}"


def test_get_github_url_only_annotation(prefix):
    """Doesn’t really work but shouldn’t crash either."""
    url = github_url("scanpydoc.rtd_github_links._TestCls.test_anno")
    assert url == f"{prefix}/rtd_github_links/__init__.py"


def test_get_obj_module():
    import sphinx.application as sa

    obj, mod = _get_obj_module("scanpydoc.Sphinx")
    assert obj is sa.Sphinx
    assert mod is sa


def test_get_obj_module_dataclass_field():
    obj, mod = _get_obj_module("scanpydoc.rtd_github_links._TestDataCls.test_attr")
    assert isinstance(obj, Field)


def test_get_obj_module_only_annotation():
    obj, mod = _get_obj_module("scanpydoc.rtd_github_links._TestCls.test_anno")
    assert obj is None

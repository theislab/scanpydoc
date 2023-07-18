from dataclasses import Field
from pathlib import Path, PurePosixPath

import pytest
from _pytest.monkeypatch import MonkeyPatch

from scanpydoc.rtd_github_links import _get_linenos, _get_obj_module, github_url


HERE = Path(__file__).parent


@pytest.fixture
def _env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("scanpydoc.rtd_github_links.github_base_url", "x")


@pytest.fixture(params=[".", "src"])
def pfx(monkeypatch: MonkeyPatch, _env, request):
    pfx = PurePosixPath(request.param)
    monkeypatch.setattr("scanpydoc.rtd_github_links.rtd_links_prefix", pfx)
    return pfx


def test_as_function(pfx):
    pth = "x" / pfx / "scanpydoc/rtd_github_links/__init__.py"
    assert github_url("scanpydoc.rtd_github_links") == str(pth)
    s, e = _get_linenos(github_url)
    assert github_url("scanpydoc.rtd_github_links.github_url") == f"{pth}#L{s}-L{e}"


def test_get_obj_module():
    import sphinx.application as sa

    obj, mod = _get_obj_module("scanpydoc.Sphinx")
    assert obj is sa.Sphinx
    assert mod is sa


def test_get_obj_module_anntation():
    obj, mod = _get_obj_module("scanpydoc.rtd_github_links._TestCls.test_attr")
    assert isinstance(obj, Field)

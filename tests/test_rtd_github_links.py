"""Test rtd_github_links subextension."""
from __future__ import annotations

import re
import sys
import textwrap
from types import ModuleType
from typing import TYPE_CHECKING
from pathlib import Path, PurePosixPath
from importlib import import_module
from dataclasses import field, dataclass

import pytest
from sphinx.config import Config

from scanpydoc import rtd_github_links
from scanpydoc.rtd_github_links import (
    github_url,
    _infer_vars,
    _get_linenos,
    _get_obj_module,
)
from scanpydoc.rtd_github_links._linkcode import CInfo, PyInfo, linkcode_resolve


if TYPE_CHECKING:
    from typing import Literal
    from collections.abc import Callable, Generator

    from sphinx.application import Sphinx
    from _pytest.monkeypatch import MonkeyPatch

    from scanpydoc.rtd_github_links._linkcode import Domain, DomainInfo


HERE = Path(__file__).parent


@pytest.fixture()
def config() -> Config:
    config = Config()
    config.add(
        "rtd_links_prefix", PurePosixPath("."), rebuild="", types=[PurePosixPath]
    )
    return config


@pytest.fixture()
def _env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("scanpydoc.rtd_github_links.github_base_url", "x")


@pytest.fixture(params=[".", "src"])
def prefix(
    monkeypatch: MonkeyPatch, _env: None, request: pytest.FixtureRequest
) -> PurePosixPath:
    pfx = PurePosixPath(request.param)
    monkeypatch.setattr("scanpydoc.rtd_github_links.rtd_links_prefix", pfx)
    return "x" / pfx / "scanpydoc"


@pytest.mark.parametrize(
    ("opt_name", "opt"),
    [
        pytest.param(
            "html_context",
            dict(
                github_user="scverse",
                github_repo="scanpydoc",
                github_version="test-branch",
            ),
            id="html_context",
        ),
        pytest.param(
            "html_theme_options",
            dict(
                repository_url="https://github.com/scverse/scanpydoc",
                repository_branch="test-branch",
            ),
            id="html_theme_options",
        ),
    ],
)
def test_infer_vars(config: Config, opt_name: str, opt: dict[str, str]) -> None:
    config.add(opt_name, {}, rebuild="", types=[dict])
    config[opt_name] = opt
    gbu, rlp = _infer_vars(config)
    assert gbu == "https://github.com/scverse/scanpydoc/tree/test-branch"
    assert rlp


PAT_VAR = r"needs html_context.*'github_user'.*or html_theme_options.*'repository_url'"


@pytest.mark.parametrize(
    ("setup", "pattern"),
    [
        pytest.param(
            [], r"needs “html_context” or “html_theme_options” to be defined", id="none"
        ),
        pytest.param(["html_context"], PAT_VAR, id="html_context"),
        pytest.param(["html_theme_options"], PAT_VAR, id="html_theme_options"),
        pytest.param(["html_context", "html_theme_options"], PAT_VAR, id="both"),
    ],
)
def test_infer_vars_error(config: Config, setup: list[str], pattern: str) -> None:
    for opt_name in setup:
        config.add(opt_name, {}, rebuild="", types=[dict])
    with pytest.raises(ValueError, match=pattern):
        _infer_vars(config)


def test_app(monkeypatch: MonkeyPatch, make_app_setup: Callable[..., Sphinx]) -> None:
    filters: dict[str, Callable[..., object]] = {}
    monkeypatch.setattr("scanpydoc.rtd_github_links._init_vars", lambda *_: None)
    monkeypatch.setattr("scanpydoc.rtd_github_links.DEFAULT_FILTERS", filters)
    app = make_app_setup(
        extensions=["sphinx.ext.linkcode", "scanpydoc.rtd_github_links"],
        html_context=dict(
            github_user="scverse", github_repo="scanpydoc", github_version="test-branch"
        ),
    )
    assert app.config["linkcode_resolve"] is linkcode_resolve
    assert filters == dict(github_url=rtd_github_links.github_url)


@pytest.mark.parametrize(
    ("module", "name", "obj_path"),
    [
        pytest.param(
            *("rtd_github_links", "github_url", "rtd_github_links/__init__.py"),
            id="basic",
        ),
        pytest.param(
            "elegant_typehints",
            "example_func_prose",
            "elegant_typehints/example.py",
            id="reexport",
        ),
    ],
)
def test_as_function(
    prefix: PurePosixPath, module: str, name: str, obj_path: str
) -> None:
    assert github_url(f"scanpydoc.{module}") == str(prefix / module / "__init__.py")
    obj = getattr(import_module(f"scanpydoc.{module}"), name)
    s, e = _get_linenos(obj)
    assert github_url(f"scanpydoc.{module}.{name}") == f"{prefix}/{obj_path}#L{s}-L{e}"


def test_get_github_url_only_annotation(prefix: PurePosixPath) -> None:
    """Doesn’t really work but shouldn’t crash either."""
    url = github_url("scanpydoc.rtd_github_links._TestCls.test_anno")
    assert url == f"{prefix}/rtd_github_links/__init__.py"


def test_get_github_url_error() -> None:
    with pytest.raises(KeyError) as exc_info:
        github_url("test.nonexistant.Thingamajig")
    if sys.version_info >= (3, 11):
        assert exc_info.value.__notes__[0] == "Qualname: 'test.nonexistant.Thingamajig'"


class _TestMod:
    modname = "testing.scanpydoc"

    @dataclass
    class TestDataCls:
        test_attr: dict[str, str] = field(default_factory=dict)

    class TestCls:
        test_anno: int


@pytest.fixture()
def test_mod() -> Generator[ModuleType, None, None]:
    mod = sys.modules[_TestMod.modname] = ModuleType(_TestMod.modname)
    for name, cls in vars(_TestMod).items():
        if isinstance(cls, type):
            cls.__module__ = _TestMod.modname
            setattr(mod, name, cls)

    try:
        yield mod
    finally:
        sys.modules.pop(_TestMod.modname, None)


@pytest.mark.parametrize(
    ("obj_path", "get_obj", "get_mod"),
    [
        pytest.param(
            "scanpydoc.indent",
            lambda _: textwrap.indent,
            lambda _: textwrap,
            id="reexport",
        ),
        pytest.param("testing.scanpydoc", lambda m: m, lambda m: m, id="mod"),
        pytest.param(
            "testing.scanpydoc.TestDataCls.test_attr",
            lambda m: m.TestDataCls.__dataclass_fields__["test_attr"],
            lambda m: m,
            id="dataclass_field",
        ),
        pytest.param(
            "testing.scanpydoc.TestCls.test_anno",
            lambda _: None,
            lambda m: m,
            id="anno",
        ),
    ],
)
def test_get_obj_module(
    test_mod: ModuleType,
    obj_path: str,
    get_obj: Callable[[ModuleType], object],
    get_mod: Callable[[ModuleType], ModuleType],
) -> None:
    obj_rcv, mod_rcv = _get_obj_module(obj_path)
    assert obj_rcv is get_obj(test_mod)
    assert mod_rcv is get_mod(test_mod)


def test_linkdoc(prefix: PurePosixPath) -> None:
    link = linkcode_resolve(
        "py", PyInfo(module="scanpydoc.rtd_github_links", fullname="setup")
    )
    assert link is not None
    url, hash_ = link.split("#")
    assert url == f"{prefix}/rtd_github_links/__init__.py"
    assert re.fullmatch(r"L\d+-L\d+", hash_)


@pytest.mark.parametrize(
    ("domain", "info"),
    [("py", PyInfo(fullname="foo", module="")), ("c", CInfo(names=[]))],
)
def test_linkcode_skip(domain: Literal[Domain], info: DomainInfo) -> None:
    assert linkcode_resolve(domain, info) is None  # type: ignore[arg-type]

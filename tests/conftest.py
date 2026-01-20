"""Custom pytest fixtures and setup."""

from __future__ import annotations

import sys
import linecache
import importlib.util
from uuid import uuid4
from typing import TYPE_CHECKING
from textwrap import dedent

import pytest


if TYPE_CHECKING:
    from types import ModuleType
    from typing import Any, NamedTuple
    from pathlib import Path
    from collections.abc import Callable, Generator

    from sphinx.testing.util import SphinxTestApp

    from scanpydoc.testing import MakeApp

    class _AppParams(NamedTuple):
        args: tuple[Any, ...]
        kwargs: dict[str, Any]


@pytest.fixture
def make_app_setup(
    tmp_path: Path, make_app: type[SphinxTestApp], app_params: _AppParams
) -> MakeApp:
    def get_builder(buildername: str = "html", **_: object) -> str:
        return buildername  # make sure there are no conflicts

    def make_app_setup(
        buildername: str | None = None,
        /,
        *,
        exception_on_warning: bool = False,
        **conf: Any,  # noqa: ANN401
    ) -> SphinxTestApp:
        (tmp_path / "conf.py").write_text("")

        if buildername is None:
            buildername = get_builder(*app_params.args, **app_params.kwargs)
            app_params.kwargs.pop("buildername", None)

        confoverrides = app_params.kwargs.get("confoverrides", {}).copy()
        confoverrides.update(conf)
        confoverrides.setdefault("suppress_warnings", []).append("app.add_node")

        return make_app(
            buildername=buildername,
            srcdir=tmp_path,
            confoverrides=confoverrides,
            warningiserror=exception_on_warning,
            exception_on_warning=exception_on_warning,
        )

    return make_app_setup


@pytest.fixture
def make_module(
    tmp_path: Path,
) -> Generator[Callable[[str, str], ModuleType], None, None]:
    added_modules = []

    def make_module(name: str, code: str) -> ModuleType:
        code = dedent(code)
        assert name not in sys.modules
        spec = importlib.util.spec_from_loader(name, loader=None)
        assert spec is not None
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

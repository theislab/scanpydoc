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
    from typing import Any
    from pathlib import Path
    from collections.abc import Callable, Generator

    from sphinx.application import Sphinx


@pytest.fixture()
def make_app_setup(
    make_app: Callable[..., Sphinx], tmp_path: Path
) -> Callable[..., Sphinx]:
    def make_app_setup(**conf: Any) -> Sphinx:  # noqa: ANN401
        (tmp_path / "conf.py").write_text("")
        return make_app(srcdir=tmp_path, confoverrides=conf)

    return make_app_setup


@pytest.fixture()
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

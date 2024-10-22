"""Test release_notes subextension."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING
from textwrap import dedent
from functools import partial

import pytest
from sphinx.errors import SphinxWarning
from docutils.utils import new_document
from docutils.languages import get_language
from docutils.parsers.rst import directives


if TYPE_CHECKING:
    from typing import Literal, TypeAlias
    from pathlib import Path
    from collections.abc import Mapping

    from sphinx.application import Sphinx
    from sphinx.testing.util import SphinxTestApp

    from scanpydoc.testing import MakeApp

    Tree: TypeAlias = Mapping[str | Path, "Tree | str"]


def mkfiles(root: Path, tree: Tree = MappingProxyType({})) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for path, sub in tree.items():
        if isinstance(sub, str):
            (root / path).write_text(sub)
        else:
            mkfiles(root / path, sub)


@pytest.fixture(params=["rst", "myst"])
def file_format(request: pytest.FixtureRequest) -> Literal["rst", "myst"]:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture
def make_app_relnotes(
    make_app_setup: MakeApp, file_format: Literal["rst", "myst"]
) -> MakeApp:
    return partial(
        make_app_setup,
        "pseudoxml",
        extensions=[
            *(["myst_parser"] if file_format == "myst" else []),
            "scanpydoc.release_notes",
        ],
        exclude_patterns=["[!i]*.md"],
    )


@pytest.fixture
def app(make_app_relnotes: MakeApp) -> SphinxTestApp:
    return make_app_relnotes()


@pytest.fixture
def index_filename(file_format: Literal["rst", "myst"]) -> str:
    return "index.md" if file_format == "myst" else "index.rst"


@pytest.fixture
def index_template(file_format: Literal["rst", "myst"]) -> str:
    return (
        "```{{release-notes}} {}\n```"
        if file_format == "myst"
        else ".. release-notes:: {}"
    )


@pytest.fixture
def files(
    file_format: Literal["rst", "myst"], index_filename: str, index_template: str
) -> Tree:
    files: Tree
    if file_format == "myst":
        files = {
            index_filename: index_template.format("."),
            "1.2.0.md": "(v1.2.0)=\n### 1.2.0",
            "1.2.1.md": "(v1.2.1)=\n### 1.2.1",
            "1.3.0rc1.md": "(v1.3.0rc1)=\n### 1.3.0rc1",
        }
    else:
        files = {
            index_filename: index_template.format("."),
            "1.2.0.rst": ".. _v1.2.0:\n1.2.0\n=====",
            "1.2.1.rst": ".. _v1.2.1:\n1.2.1\n=====",
            "1.3.0rc1.rst": ".. _v1.3.0rc1:\n1.3.0rc1\n========",
        }
    return files


expected = """\
<target refid="v1-3">
<section ids="version-1-3 v1-3" names="version\\ 1.3 v1.3">
    <title>
        Version 1.3
    <target refid="v1-3-0rc1">
    <section ids="rc1 v1-3-0rc1" names="1.3.0rc1 v1.3.0rc1">
        <title>
            1.3.0rc1
<target refid="v1-2">
<section ids="version-1-2 v1-2" names="version\\ 1.2 v1.2">
    <title>
        Version 1.2
    <target refid="v1-2-1">
    <section ids="v1-2-1 id1" names="1.2.1 v1.2.1">
        <title>
            1.2.1
    <target refid="v1-2-0">
    <section ids="v1-2-0 id2" names="1.2.0 v1.2.0">
        <title>
            1.2.0
"""


def test_release_notes(tmp_path: Path, app: Sphinx, files: Tree) -> None:
    mkfiles(tmp_path, files)
    app.build()
    index_out = (tmp_path / "_build/pseudoxml/index.pseudoxml").read_text()
    assert (
        "\n".join(l[4:] for l in dedent(index_out).splitlines()[1:]) == expected.strip()
    )


@pytest.mark.parametrize(
    ("root", "files", "pattern"),
    [
        pytest.param(
            "doesnt-exist.txt", {}, r"Not a directory:.*doesnt-exist.txt", id="nothing"
        ),
        pytest.param(
            "file.txt", {"file.txt": "cont"}, r"Not a directory:.*file.txt", id="file"
        ),
    ],
)
def test_error_wrong_file(
    tmp_path: Path,
    make_app_relnotes: MakeApp,
    index_filename: str,
    index_template: str,
    root: str,
    files: Tree,
    pattern: str,
) -> None:
    app = make_app_relnotes(exception_on_warning=True)
    mkfiles(tmp_path, {index_filename: index_template.format(root), **files})
    with pytest.raises(SphinxWarning, match=pattern):
        app.build()


def test_error_no_src(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    make_app_relnotes: MakeApp,
    files: Tree,
) -> None:
    app = make_app_relnotes(exception_on_warning=True)
    if "myst_parser" not in app.extensions:
        pytest.skip("rst parser doesn’t need this")
    rn, _ = directives.directive("release-notes", get_language("en"), new_document(""))
    monkeypatch.setattr(rn, "get_source_info", lambda *_, **__: ("<string>", 0))

    mkfiles(tmp_path, files)
    with pytest.raises(SphinxWarning, match=r"Cannot find relative path to: <string>"):
        app.build()

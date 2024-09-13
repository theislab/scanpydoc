"""Test release_notes subextension."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING
from textwrap import dedent

import pytest
from sphinx.errors import SphinxWarning
from docutils.utils import new_document
from docutils.languages import get_language
from docutils.parsers.rst import directives


if TYPE_CHECKING:
    from typing import TypeAlias
    from pathlib import Path
    from collections.abc import Mapping, Callable

    from pytest_mock import MockerFixture
    from sphinx.application import Sphinx

    Tree: TypeAlias = Mapping[str | Path, "Tree | str"]


def mkfiles(root: Path, tree: Tree = MappingProxyType({})) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for path, sub in tree.items():
        if isinstance(sub, str):
            (root / path).write_text(sub)
        else:
            mkfiles(root / path, sub)


@pytest.fixture(params=["rst", "myst"])
def app(
    request: pytest.FixtureRequest, make_app_setup: Callable[..., Sphinx]
) -> Sphinx:
    return make_app_setup(
        "pseudoxml",
        extensions=[
            *(["myst_parser"] if request.param == "myst" else []),
            "scanpydoc.release_notes",
        ],
        exclude_patterns=["[!i]*.md"],
    )


@pytest.fixture
def index_filename(app: Sphinx) -> str:
    return "index.md" if "myst_parser" in app.extensions else "index.rst"


@pytest.fixture
def index_template(app: Sphinx) -> str:
    return (
        "```{{release-notes}} {}\n```"
        if "myst_parser" in app.extensions
        else ".. release-notes:: {}"
    )


@pytest.fixture
def files(app: Sphinx, index_filename: str, index_template: str) -> Tree:
    files: Tree
    if "myst_parser" in app.extensions:
        files = {
            index_filename: index_template.format("."),
            "1.2.0.md": "### 1.2.0",
            "1.2.1.md": "### 1.2.1",
            "1.3.0.md": "### 1.3.0",
            "1.3.2.md": "### 1.3.2",
        }
    else:
        files = {
            index_filename: index_template.format("."),
            "1.2.0.rst": "1.2.0\n=====",
            "1.2.1.rst": "1.2.1\n=====",
            "1.3.0.rst": "1.3.0\n=====",
            "1.3.2.rst": "1.3.2\n=====",
        }
    return files


expected = """\
<target refid="v1-3">
<section ids="version-1-3 v1-3" names="version\\ 1.3 v1.3">
    <title>
        Version 1.3
    <section ids="id1" names="1.3.2">
        <title>
            1.3.2
    <section ids="id2" names="1.3.0">
        <title>
            1.3.0
<target refid="v1-2">
<section ids="version-1-2 v1-2" names="version\\ 1.2 v1.2">
    <title>
        Version 1.2
    <section ids="id3" names="1.2.1">
        <title>
            1.2.1
    <section ids="id4" names="1.2.0">
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
    app: Sphinx,
    index_filename: str,
    index_template: str,
    root: str,
    files: Tree,
    pattern: str,
) -> None:
    mkfiles(tmp_path, {index_filename: index_template.format(root), **files})
    app.warningiserror = True
    with pytest.raises(SphinxWarning, match=pattern):
        app.build()


def test_error_no_src(
    mocker: MockerFixture,
    tmp_path: Path,
    app: Sphinx,
    files: Tree,
) -> None:
    if "myst_parser" not in app.extensions:
        pytest.skip("rst parser doesn’t need this")
    app.warningiserror = True
    rn, _ = directives.directive("release-notes", get_language("en"), new_document(""))
    mocker.patch.object(rn, "get_source_info", return_value=("<string>", 0))

    mkfiles(tmp_path, files)
    with pytest.raises(SphinxWarning, match=r"Cannot find relative path to: <string>"):
        app.build()

from typing import Mapping, Any, Dict, Union

import pytest
from sphinx.application import Sphinx

from scanpydoc import elegant_typehints
from scanpydoc.elegant_typehints import format_annotation, _format_terse, _format_full


@pytest.fixture
def app(app_no_setup) -> Sphinx:
    elegant_typehints.setup(app_no_setup)
    return app_no_setup


def test_default(app):
    assert format_annotation(str) == ":py:class:`str`"


def test_alternatives(app):
    def process_docstring(a):
        """Caller needs to be `process_docstring` to create both formats"""
        return format_annotation(a)

    assert process_docstring(str) == (
        r":annotation-terse:`:py:class:\`str\``\ "
        r":annotation-full:`:py:class:\`str\``"
    )


def test_mapping(app):
    assert _format_terse(Mapping[str, Any]) == ":py:class:`~typing.Mapping`"
    assert _format_full(Mapping[str, Any]) == (
        r":py:class:`~typing.Mapping`\["
        r":py:class:`str`, "
        r":py:data:`~typing.Any`"
        r"]"
    )


def test_dict(app):
    assert _format_terse(Dict[str, Any]) == "{:py:class:`str`: :py:data:`~typing.Any`}"


def test_qualname_overrides(app):
    sparse = pytest.importorskip("scipy.sparse")

    assert sparse.spmatrix.__module__ == "scipy.sparse.base"
    assert _format_terse(sparse.spmatrix) == ":py:class:`~scipy.sparse.spmatrix`"


def test_qualname_overrides_recursive(app):
    sparse = pytest.importorskip("scipy.sparse")

    assert _format_terse(Union[sparse.spmatrix, str]) == (
        r":py:class:`~scipy.sparse.spmatrix`, :py:class:`str`"
    )
    assert _format_full(Union[sparse.spmatrix, str]) == (
        r":py:data:`~typing.Union`\["
        r":py:class:`~scipy.sparse.spmatrix`, "
        r":py:class:`str`"
        r"]"
    )


def test_fully_qualified(app):
    sparse = pytest.importorskip("scipy.sparse")

    assert _format_terse(Union[sparse.spmatrix, str], True) == (
        r":py:class:`scipy.sparse.spmatrix`, :py:class:`str`"
    )
    assert _format_full(Union[sparse.spmatrix, str], True) == (
        r":py:data:`typing.Union`\["
        r":py:class:`scipy.sparse.spmatrix`, "
        r":py:class:`str`"
        r"]"
    )


def test_classes_get_added(app, parse):
    doc = parse(app, r":annotation-full:`:py:class:\`str\``")
    assert doc[0].tagname == "paragraph"
    assert doc[0][0].tagname == "inline"
    assert doc[0][0]["classes"] == ["annotation", "full"]
    # print(doc.asdom().toprettyxml())

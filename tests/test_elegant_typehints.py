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
        ":annotation-terse:`:py:class:\\`str\\``\\ "
        ":annotation-full:`:py:class:\\`str\\``"
    )


def test_mapping(app):
    assert _format_terse(Mapping[str, Any]) == ":py:class:`~typing.Mapping`"
    assert _format_full(Mapping[str, Any]) == (
        ":py:class:`~typing.Mapping`\\["
        ":py:class:`str`, "
        ":py:data:`~typing.Any`"
        "]"
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
        ":py:class:`~scipy.sparse.spmatrix`, " ":py:class:`str`"
    )
    assert _format_full(Union[sparse.spmatrix, str]) == (
        ":py:data:`~typing.Union`\\["
        ":py:class:`~scipy.sparse.spmatrix`, "
        ":py:class:`str`"
        "]"
    )

from typing import Mapping, Any, Dict

from scanpydoc.elegant_typehints import format_annotation, _format_terse, _format_full


def test_default():
    assert format_annotation(str) == ":py:class:`str`"


def test_alternatives():
    def process_docstring(a):
        """Caller needs to be `process_docstring` to create both formats"""
        return format_annotation(a)

    assert process_docstring(str) == (
        ":annotation-terse:`:py:class:\\`str\\``\\ "
        ":annotation-full:`:py:class:\\`str\\``"
    )


def test_mapping():
    assert _format_terse(Mapping[str, Any]) == ":py:class:`~typing.Mapping`"
    assert _format_full(Mapping[str, Any]) == (
        ":py:class:`~typing.Mapping`\\[:py:class:`str`, :py:data:`~typing.Any`]"
    )


def test_dict():
    assert _format_terse(Dict[str, Any]) == "{:py:class:`str`: :py:data:`~typing.Any`}"

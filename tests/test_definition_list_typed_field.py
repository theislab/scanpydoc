"""Test definition_list_typed_field subextension."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sphinx.testing.restructuredtext import parse


if TYPE_CHECKING:
    from collections.abc import Callable

    from sphinx.application import Sphinx


@pytest.fixture()
def app(make_app_setup: Callable[..., Sphinx]) -> Sphinx:
    app = make_app_setup()
    app.setup_extension("scanpydoc.definition_list_typed_field")
    return app


# Avoid :class: to not get pending_xref. TODO: fix
params_code = """\
.. py:function:: test(a, b=None)

   :param a: First parameter
   :type a: ``str``
   :param b: Second parameter
   :type v: ``~typing.Optional``\\[``str``]
"""

params_code_single = """\
.. py:function:: test(a)

   :param a: First parameter
   :type a: ``str``
"""


def test_apps_separate(app: Sphinx, make_app_setup: Callable[..., Sphinx]) -> None:
    app_no_setup = make_app_setup()
    assert app is not make_app_setup
    assert "scanpydoc.definition_list_typed_field" in app.extensions
    assert "scanpydoc.definition_list_typed_field" not in app_no_setup.extensions


@pytest.mark.parametrize(("code", "n"), [(params_code, 2), (params_code_single, 1)])
def test_convert_params(app: Sphinx, code: str, n: int) -> None:
    # the directive class is PyModuleLevel → PyObject → ObjectDescription
    # ObjectDescription.run uses a DocFieldTransformer to transform members
    # the signature of each Directive(
    #     name, arguments, options, content, lineno,
    #     content_offset, block_text, state, state_machine,

    doc = parse(app, code)
    assert doc[1].tagname == "desc"
    assert doc[1]["desctype"] == "function"
    assert doc[1][1].tagname == "desc_content"
    assert doc[1][1][0].tagname == "field_list"
    assert doc[1][1][0][0].tagname == "field"
    assert doc[1][1][0][0][0].tagname == "field_name"
    assert doc[1][1][0][0][0][0].astext() == "Parameters"
    assert doc[1][1][0][0][1].tagname == "field_body"
    assert doc[1][1][0][0][1][0].tagname == "definition_list"

    dl = doc[1][1][0][0][1][0]
    assert len(dl) == n, dl
    for dli in dl:
        assert dli.tagname == "definition_list_item"
        assert dli[0].tagname == "term"
        assert dli[1].tagname == "definition"

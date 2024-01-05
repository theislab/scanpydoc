"""Test definition_list_typed_field subextension."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sphinx import addnodes
from docutils import nodes
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
params_code_single = """\
.. py:function:: test(a)

   :param a: Only parameter
   :type a: ``str``
"""

params_code = """\
.. py:function:: test(a, b=None)

   :param a: First parameter
   :type a: str
   :param b: Second parameter
   :type b: ``~typing.Optional``\\[``str``]
"""


def test_apps_separate(app: Sphinx, make_app_setup: Callable[..., Sphinx]) -> None:
    app_no_setup = make_app_setup()
    assert app is not app_no_setup
    assert "scanpydoc.definition_list_typed_field" in app.extensions
    assert "scanpydoc.definition_list_typed_field" not in app_no_setup.extensions


@pytest.mark.parametrize(
    ("code", "n", "i", "conv_types"),
    [
        pytest.param(params_code_single, 1, 0, [nodes.literal], id="1-simple"),
        pytest.param(params_code, 2, 0, [addnodes.pending_xref], id="2-refconv"),
        pytest.param(
            params_code,
            2,
            1,
            [nodes.literal, nodes.Text, nodes.literal, nodes.Text],
            id="2-multi",
        ),
    ],
)
def test_convert_params(
    app: Sphinx, code: str, n: int, i: int, conv_types: list[type[nodes.Node]]
) -> None:
    # the directive class is PyModuleLevel → PyObject → ObjectDescription
    # ObjectDescription.run uses a DocFieldTransformer to transform members
    # the signature of each Directive(
    #     name, arguments, options, content, lineno,
    #     content_offset, block_text, state, state_machine,

    doc = parse(app, code)
    assert isinstance(desc := doc[1], addnodes.desc)
    assert desc["desctype"] == "function"
    assert isinstance(desc_content := desc[1], addnodes.desc_content)
    assert isinstance(field_list := desc_content[0], nodes.field_list)
    assert isinstance(field := field_list[0], nodes.field)
    assert isinstance(field_name := field[0], nodes.field_name)
    assert isinstance(field_name_text := field_name[0], nodes.Text)
    assert field_name_text.astext() == "Parameters"
    assert isinstance(field_body := field[1], nodes.field_body)
    assert isinstance(dl := field_body[0], nodes.definition_list)

    # each parameter is a dl item that contains a term and a definition
    assert len(dl) == n, dl.children
    assert isinstance(dli := dl[i], nodes.definition_list_item)
    assert isinstance(term := dli[0], nodes.term)
    assert isinstance(dli[1], nodes.definition)

    # the dl term contains the parameter name and type
    assert len(term) == 3, term.children  # noqa: PLR2004
    assert isinstance(term[0], addnodes.literal_strong)
    assert isinstance(term[1], nodes.Text)
    assert term[1].astext() == " "  # spacer
    assert isinstance(cyr := term[2], nodes.classifier)
    assert len(cyr) == len(conv_types), cyr.children
    assert all(
        isinstance(cyr_part, conv_type) for cyr_part, conv_type in zip(cyr, conv_types)
    )


def test_load_error(make_app_setup: Callable[..., Sphinx]) -> None:
    with pytest.raises(RuntimeError, match=r"Please load sphinx\.ext\.napoleon before"):
        make_app_setup(
            extensions=["scanpydoc.definition_list_typed_field", "sphinx.ext.napoleon"]
        )

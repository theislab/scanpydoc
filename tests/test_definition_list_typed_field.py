import pytest
from sphinx.application import Sphinx
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.writers.html import HTMLTranslator, HTMLWriter
from sphinx.writers.html5 import HTML5Translator

from scanpydoc import definition_list_typed_field


@pytest.fixture
def app(app_no_setup) -> Sphinx:
    definition_list_typed_field.setup(app_no_setup)
    return app_no_setup


# Avoid :class: to not get pending_xref. TODO: fix
params_code = """\
.. py:function:: test(a, b=None)

   :param a: First parameter
   :type a: ``str``
   :param b: Second parameter
   :type v: ``~typing.Optional``\\[``str``]
"""


def test_convert_params(app, parse):
    # the directive class is PyModuleLevel → PyObject → ObjectDescription
    # ObjectDescription.run uses a DocFieldTransformer to transform members
    # the signature of each Directive(
    #     name, arguments, options, content, lineno,
    #     content_offset, block_text, state, state_machine,
    # )

    doc = parse(app, params_code)
    assert doc[1]["desctype"] == "function"
    assert doc[1][1].tagname == "desc_content"
    assert doc[1][1][0].tagname == "field_list"
    assert doc[1][1][0][0].tagname == "field"
    assert doc[1][1][0][0][0].tagname == "field_name"
    assert doc[1][1][0][0][0][0].astext() == "Parameters"
    assert doc[1][1][0][0][1].tagname == "field_body"
    assert doc[1][1][0][0][1][0].tagname == "definition_list"

    dl = doc[1][1][0][0][1][0]
    assert len(dl) == 2
    assert dl[0].tagname == dl[1].tagname == "definition_list_item"
    assert dl[0][0].tagname == dl[1][0].tagname == "term"
    assert dl[0][1].tagname == dl[1][1].tagname == "definition"

    # print(doc.asdom().toprettyxml())


def test_render_params_html4(app, parse, render):
    app.config.html_experimental_html5_writer = False
    assert app.builder.__class__ is StandaloneHTMLBuilder
    assert app.builder.default_translator_class is HTMLTranslator

    doc = parse(app, params_code)
    html = render(app, doc)
    assert "<dl" in html


def test_render_params_html5(app, parse, render):
    app.config.html_experimental_html5_writer = True
    assert app.builder.__class__ is StandaloneHTMLBuilder
    assert app.builder.default_translator_class is HTML5Translator

    doc = parse(app, params_code)
    html = render(app, doc)
    assert "<dl" in html

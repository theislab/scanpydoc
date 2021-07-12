"""Prettier function parameter documentation.

This extension replaces the default :class:`~sphinx.domains.python.PyTypedField`
with a derivative :class:`DLTypedField`, which renders item items
(e.g. function parameters) as definition lists instead of simple paragraphs.
"""

from typing import Dict, List, Tuple, Any

from docutils import nodes
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.domains.python import PyTypedField, PyObject
from sphinx.environment import BuildEnvironment

from . import _setup_sig, metadata


class DLTypedField(PyTypedField):
    """A reStructuredText field-list renderer that creates definition lists.

    This style is more readable than cramming name, type, and description in one line.

    The class is not intended to be used directly, but by using the extension,
    it will be used instead of the default :class:`~sphinx.domains.python.PyTypedField`.
    """

    #: Override the list type
    list_type = nodes.definition_list

    def make_field(
        self,
        types: Dict[str, List[nodes.Node]],
        domain: str,
        items: Tuple[str, List[nodes.inline]],
        env: BuildEnvironment = None,
        **kw,
    ) -> nodes.field:
        """Render a field to a document-tree node representing a definition list item."""

        def make_refs(role_name, name, node):
            return self.make_xrefs(role_name, domain, name, node, env=env, **kw)

        def handle_item(
            fieldarg: str, content: List[nodes.inline]
        ) -> nodes.definition_list_item:
            head = nodes.term()
            head += make_refs(self.rolename, fieldarg, addnodes.literal_strong)
            field_type = types.pop(fieldarg, None)
            if field_type is not None:
                head += nodes.Text(" : ")
                if len(field_type) == 1 and isinstance(field_type[0], nodes.Text):
                    (text_node,) = field_type  # type: nodes.Text
                    head += make_refs(
                        self.typerolename, text_node.astext(), addnodes.literal_emphasis
                    )
                else:
                    head += field_type

            body_content = nodes.paragraph("", "", *content)
            body = nodes.definition("", body_content)

            return nodes.definition_list_item("", head, body)

        field_name = nodes.field_name("", self.label)
        assert not self.can_collapse
        body_node = self.list_type()
        for field_arg, content in items:
            body_node += handle_item(field_arg, content)
        field_body = nodes.field_body("", body_node)
        return nodes.field("", field_name, field_body)


@_setup_sig
def setup(app: Sphinx) -> Dict[str, Any]:
    """Replace :class:`~sphinx.domains.python.PyTypedField` with ours."""
    napoleon_requested = "sphinx.ext.napoleon" in app.config.extensions
    napoleon_loaded = next(
        (True for ft in PyObject.doc_field_types if ft.name == "keyword"), False
    )
    if napoleon_requested and not napoleon_loaded:
        raise RuntimeError(f"Please load sphinx.ext.napoleon before {__name__}")

    PyObject.doc_field_types = [
        DLTypedField(
            ft.name,
            names=ft.names,
            typenames=ft.typenames,
            label=ft.label,
            rolename=ft.rolename,
            typerolename=ft.typerolename,
            # Definition lists can’t collapse.
            can_collapse=False,
        )
        if isinstance(ft, PyTypedField)
        else ft
        for ft in PyObject.doc_field_types
    ]

    return metadata

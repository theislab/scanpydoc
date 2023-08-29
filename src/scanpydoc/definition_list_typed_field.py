"""Prettier function parameter documentation.

This extension replaces the default :class:`~sphinx.domains.python.PyTypedField`
with a derivative :class:`DLTypedField`, which renders item items
(e.g. function parameters) as definition lists instead of simple paragraphs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docutils import nodes
from sphinx import addnodes
from sphinx.domains.python import PyObject, PyTypedField

from . import _setup_sig, metadata


if TYPE_CHECKING:
    from typing import Any, TypeAlias

    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment

    TextLikeNode: TypeAlias = nodes.Text | nodes.TextElement


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
        types: dict[str, list[nodes.Node]],
        domain: str,
        items: tuple[str, list[nodes.inline]],
        env: BuildEnvironment | None = None,
        **kw,  # noqa: ANN003
    ) -> nodes.field:
        """Render a field to a documenttree node representing a definition list item."""

        def make_refs(
            role_name: str,
            name: str,
            node: type[TextLikeNode],
        ) -> list[nodes.Node]:
            return self.make_xrefs(role_name, domain, name, node, env=env, **kw)

        def handle_item(
            fieldarg: str,
            content: list[nodes.inline],
        ) -> nodes.definition_list_item:
            term = nodes.term()
            term += make_refs(self.rolename, fieldarg, addnodes.literal_strong)

            field_type = types.pop(fieldarg, None)
            if field_type is not None:
                if len(field_type) == 1 and isinstance(field_type[0], nodes.Text):
                    (text_node,) = field_type  # type: nodes.Text
                    classifier_content = make_refs(
                        self.typerolename,
                        text_node.astext(),
                        addnodes.literal_emphasis,
                    )
                else:
                    classifier_content = field_type
                term += [
                    # https://github.com/sphinx-doc/sphinx/issues/10815
                    nodes.Text(" "),
                    # Sphinx tries to fixup classifiers without rawsource,
                    # but for this expects attributes we don’t have. Thus “×”.
                    nodes.classifier("×", "", *classifier_content),
                ]

            def_content = nodes.paragraph("", "", *content)
            definition = nodes.definition("", def_content)

            return nodes.definition_list_item("", term, definition)

        field_name = nodes.field_name("", self.label)
        assert not self.can_collapse  # noqa: S101
        body_node = self.list_type(classes=["simple"])
        for field_arg, content in items:
            body_node += handle_item(field_arg, content)
        field_body = nodes.field_body("", body_node)
        return nodes.field("", field_name, field_body)


@_setup_sig
def setup(app: Sphinx) -> dict[str, Any]:
    """Replace :class:`~sphinx.domains.python.PyTypedField` with ours."""
    napoleon_requested = "sphinx.ext.napoleon" in app.config.extensions
    napoleon_loaded = next(
        (True for ft in PyObject.doc_field_types if ft.name == "keyword"),
        False,
    )
    if napoleon_requested and not napoleon_loaded:
        msg = f"Please load sphinx.ext.napoleon before {__name__}"
        raise RuntimeError(msg)

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

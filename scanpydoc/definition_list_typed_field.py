"""Prettier Param docs

Our DLTypedField is the same as the default PyTypedField,
except that the items (e.g. function parameters) get rendered as
definition list instead of paragraphs with some formatting.
"""

from typing import Dict, List, Tuple, Any

from docutils import nodes
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.domains.python import PyTypedField, PyObject
from sphinx.environment import BuildEnvironment


class DLTypedField(PyTypedField):
    list_type = nodes.definition_list

    def make_field(
        self,
        types: Dict[str, List[nodes.Node]],
        domain: str,
        items: Tuple[str, List[nodes.inline]],
        env: BuildEnvironment = None,
    ) -> nodes.field:
        def makerefs(rolename, name, node):
            return self.make_xrefs(rolename, domain, name, node, env=env)

        def handle_item(
            fieldarg: str, content: List[nodes.inline]
        ) -> nodes.definition_list_item:
            head = nodes.term()
            head += makerefs(self.rolename, fieldarg, addnodes.literal_strong)
            fieldtype = types.pop(fieldarg, None)
            if fieldtype is not None:
                head += nodes.Text(" : ")
                if len(fieldtype) == 1 and isinstance(fieldtype[0], nodes.Text):
                    text_node, = fieldtype  # type: nodes.Text
                    head += makerefs(
                        self.typerolename, text_node.astext(), addnodes.literal_emphasis
                    )
                else:
                    head += fieldtype

            body_content = nodes.paragraph("", "", *content)
            body = nodes.definition("", body_content)

            return nodes.definition_list_item("", head, body)

        fieldname = nodes.field_name("", self.label)
        if len(items) == 1 and self.can_collapse:
            fieldarg, content = items[0]
            bodynode = handle_item(fieldarg, content)
        else:
            bodynode = self.list_type()
            for fieldarg, content in items:
                bodynode += handle_item(fieldarg, content)
        fieldbody = nodes.field_body("", bodynode)
        return nodes.field("", fieldname, fieldbody)


def setup(app: Sphinx) -> Dict[str, Any]:
    """replace matching field types with ours"""
    PyObject.doc_field_types = [
        DLTypedField(
            ft.name,
            names=ft.names,
            typenames=ft.typenames,
            label=ft.label,
            rolename=ft.rolename,
            typerolename=ft.typerolename,
            can_collapse=ft.can_collapse,
        )
        if isinstance(ft, PyTypedField)
        else ft
        for ft in PyObject.doc_field_types
    ]

    from . import metadata

    return metadata

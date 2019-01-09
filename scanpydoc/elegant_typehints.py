# -*- coding: future-fstrings -*-
"""Format typehints elegantly and and fix autimatically created links.

The Sphinx extension :mod:`sphinx_autodoc_typehints` adds type annotations to functions.
This extension modifies the created type annotations in two ways:

#. It formats the annotations more simply and in line with e.g. :mod:`numpy`.
#. It defines a configuration value ``qualname_overrides`` for ``conf.py``
   that overrides automatically created links. It is used like this::

       qualname_overrides = {
           "pandas.core.frame.DataFrame": "pandas.DataFrame",
           ...,
       }

   The defaults include :class:`anndata.AnnData`, :class:`pandas.DataFrame`,
   :class:`scipy.sparse.spmatrix` and other classes in :mod:`scipy.sparse`.

   It is necessary since :attr:`~definition.__qualname__` does not necessarily match
   the documented location of the function/class.

   Once either `sphinx issue 4826`_ or `sphinx-autodoc-typehints issue 38`_ are fixed,
   this part of the functionality will no longer be necessary.

.. _sphinx issue 4826: https://github.com/sphinx-doc/sphinx/issues/4826
.. _sphinx-autodoc-typehints issue 38: https://github.com/agronholm/sphinx-autodoc-typehints/issues/38

"""
import inspect
from collections import abc, ChainMap
from functools import partial
from pathlib import Path
from typing import Any, Union, Optional  # Meta
from typing import Type, Mapping, Sequence  # ABC
from typing import Dict, List, Tuple  # Concrete

import sphinx_autodoc_typehints
from sphinx_autodoc_typehints import format_annotation as _format_full
from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst.roles import set_classes
from docutils.parsers.rst.states import Inliner, Struct
from docutils.utils import SystemMessage, unescape
from sphinx.application import Sphinx
from sphinx.config import Config
from docutils.parsers.rst import roles

from . import _setup_sig, metadata


HERE = Path(__file__).parent.resolve()

qualname_overrides_default = {
    "anndata.base.AnnData": "anndata.AnnData",
    "pandas.core.frame.DataFrame": "pandas.DataFrame",
    "scipy.sparse.base.spmatrix": "scipy.sparse.spmatrix",
    "scipy.sparse.csr.csr_matrix": "scipy.sparse.csr_matrix",
    "scipy.sparse.csc.csc_matrix": "scipy.sparse.csc_matrix",
}
qualname_overrides = ChainMap({}, qualname_overrides_default)


def _init_vars(app: Sphinx, config: Config):
    qualname_overrides.update(config.qualname_overrides)
    config.html_static_path.append(str(HERE / "static"))


def _format_terse(annotation: Type[Any]) -> str:
    union_params = getattr(annotation, "__union_params__", None)

    # display `Union[A, B]` as `A, B`
    if getattr(annotation, "__origin__", None) is Union or union_params:
        params = union_params or getattr(annotation, "__args__", None)
        # Never use the `Optional` keyword in the displayed docs.
        # Use the more verbose `, None` instead,
        # as is the convention in the other large numerical packages
        # if len(params or []) == 2 and getattr(params[1], '__qualname__', None) == 'NoneType':
        #     return fa_orig(annotation)  # Optional[...]
        return ", ".join(map(_format_terse, params))

    # do not show the arguments of Mapping
    if getattr(annotation, "__origin__", None) in (abc.Mapping, Mapping):
        return ":py:class:`~typing.Mapping`"

    # display dict as {k: v}
    if getattr(annotation, "__origin__", None) in (dict, Dict):
        k, v = annotation.__args__
        return f"{{{_format_terse(k)}: {_format_terse(v)}}}"

    if inspect.isclass(annotation):
        full_name = f"{annotation.__module__}.{annotation.__qualname__}"
        override = qualname_overrides.get(full_name)
        if override is not None:
            return f":py:class:`~{override}`"
    return _format_full(annotation)


def format_annotation(annotation: Type[Any]) -> str:
    """Generate reStructuredText containing links to the types.

    Unlike :func:`sphinx_autodoc_typehints.format_annotation`,
    it tries to achieve a simpler style as seen in numeric packages like numpy.

    Args:
        annotation: A type or class used as type annotation.

    Returns:
        reStructuredText describing the type
    """

    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    if calframe[1][3] == "process_docstring":
        return (
            f":annotation-terse:`{_escape(_format_terse(annotation))}`\\ "
            f":annotation-full:`{_escape(_format_full(annotation))}`"
        )
    else:  # recursive use
        return _format_full(annotation)


def _role_annot(
    name: str,
    rawtext: str,
    text: str,
    lineno: int,
    inliner: Inliner,
    options: Dict[str, Any] = {},
    content: Sequence[str] = (),
    # *,  # https://github.com/ambv/black/issues/613
    additional_class: Optional[str] = None,
) -> Tuple[List[Node], List[SystemMessage]]:
    options = options.copy()
    set_classes(options)
    if additional_class is not None:
        options["classes"] = options.get("classes", []).copy()
        options["classes"].append(additional_class)
    memo = Struct(
        document=inliner.document, reporter=inliner.reporter, language=inliner.language
    )
    node = nodes.inline(unescape(rawtext), "", **options)
    children, messages = inliner.parse(_unescape(text), lineno, memo, node)
    node.extend(children)
    return [node], messages


def _escape(rst: str) -> str:
    return rst.replace("`", "\\`")


def _unescape(rst: str) -> str:
    # TODO: IDK why the [ part is necessary.
    return unescape(rst).replace("\\`", "`").replace("[", "\\[")


@_setup_sig
def setup(app: Sphinx) -> Dict[str, Any]:
    """Patches :mod:`sphinx_autodoc_typehints` for a more elegant display."""
    app.add_config_value("qualname_overrides", {}, "")
    app.add_css_file("typehints.css")
    app.connect("config-inited", _init_vars)
    sphinx_autodoc_typehints.format_annotation = format_annotation
    for name in ["annotation-terse", "annotation-full"]:
        roles.register_canonical_role(name, partial(_role_annot, additional_class=name))

    return metadata

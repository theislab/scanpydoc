"""Format typehints elegantly and and fix automatically created links.

The Sphinx extension :mod:`sphinx_autodoc_typehints` adds type annotations to functions.
This extension modifies the created type annotations in four ways:

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
#. The config value ``annotate_defaults`` (default: :data:`True`) controls if rST code
   like ``(default: `42`)`` is added after the type.
#. Type annotations for :class:`tuple` return types are added::

       def x() -> Tuple[int, float]:
           \"""
           Returns:
               a: An integer
               b: A floating point number
           \"""

   will render as:

       :Returns: a : :class:`int`
                     An integer
                 b : :class:`float`
                     A floating point number


.. _sphinx issue 4826: https://github.com/sphinx-doc/sphinx/issues/4826
.. _sphinx-autodoc-typehints issue 38: https://github.com/agronholm/sphinx-autodoc-typehints/issues/38

"""
from collections import ChainMap
from functools import partial
from pathlib import Path
from typing import Any, Dict


import sphinx_autodoc_typehints
from sphinx.application import Sphinx
from sphinx.config import Config
from docutils.parsers.rst import roles
from sphinx.ext.autodoc import ClassDocumenter

from .. import _setup_sig, metadata
from .example import example_func


HERE = Path(__file__).parent.resolve()

qualname_overrides_default = {
    "anndata.base.AnnData": "anndata.AnnData",
    "anndata.core.anndata.AnnData": "anndata.AnnData",
    "anndata._core.anndata.AnnData": "anndata.AnnData",
    "matplotlib.axes._axes.Axes": "matplotlib.axes.Axes",
    "pandas.core.frame.DataFrame": "pandas.DataFrame",
    "pandas.core.indexes.base.Index": "pandas.Index",
    "scipy.sparse.base.spmatrix": "scipy.sparse.spmatrix",
    "scipy.sparse.csr.csr_matrix": "scipy.sparse.csr_matrix",
    "scipy.sparse.csc.csc_matrix": "scipy.sparse.csc_matrix",
}
qualname_overrides = ChainMap({}, qualname_overrides_default)
annotate_defaults = True


def _init_vars(app: Sphinx, config: Config):
    global annotate_defaults
    qualname_overrides.update(config.qualname_overrides)
    annotate_defaults = config.annotate_defaults
    config.html_static_path.append(str(HERE / "static"))


example_func.__module__ = "scanpydoc.elegant_typehints"  # Make it show up here


@_setup_sig
def setup(app: Sphinx) -> Dict[str, Any]:
    """Patches :mod:`sphinx_autodoc_typehints` for a more elegant display."""
    # TODO: Unsure if “html” is sufficient or if we need to do “env”;
    #       Depends on when the autodoc-process-docstring event is handled.
    app.add_config_value("qualname_overrides", {}, "html")
    app.add_config_value("annotate_defaults", True, "html")
    app.add_css_file("typehints.css")
    app.connect("config-inited", _init_vars)

    from .formatting import format_annotation, _role_annot

    sphinx_autodoc_typehints.format_annotation = format_annotation
    for name in ["annotation-terse", "annotation-full"]:
        roles.register_canonical_role(
            name, partial(_role_annot, additional_classes=name.split("-"))
        )

    from .autodoc_patch import dir_head_adder

    ClassDocumenter.add_directive_header = dir_head_adder(
        qualname_overrides, ClassDocumenter.add_directive_header
    )

    from .return_tuple import process_docstring  # , process_signature

    app.connect("autodoc-process-docstring", process_docstring)
    # app.connect("autodoc-process-signature", process_signature)

    return metadata

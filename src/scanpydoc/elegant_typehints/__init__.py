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
   It sets sphinx-autodoc-typehints’s option ``typehints_defaults`` to ``'braces'``
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
.. _sphinx-autodoc-typehints issue 38: https://github.com/tox-dev/sphinx-autodoc-typehints/issues/38

"""  # noqa: D300

from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path
from collections import ChainMap
from dataclasses import dataclass

from sphinx.ext.autodoc import ClassDocumenter

from scanpydoc import metadata, _setup_sig

from .example import (
    example_func_prose,
    example_func_tuple,
    example_func_anonymous_tuple,
)


if TYPE_CHECKING:
    from typing import Any
    from collections.abc import Callable

    from sphinx.config import Config
    from sphinx.application import Sphinx


__all__ = [
    "example_func_anonymous_tuple",
    "example_func_prose",
    "example_func_tuple",
    "setup",
]


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


def _init_vars(_app: Sphinx, config: Config) -> None:
    qualname_overrides.update(config.qualname_overrides)
    if (
        "sphinx_autodoc_typehints" in config.extensions
        and config.typehints_defaults is None
        and config.annotate_defaults
    ):
        # override default for “typehints_defaults”
        config.typehints_defaults = "braces"


@dataclass
class PickleableCallable:
    func: Callable[..., Any]

    __call__ = property(lambda self: self.func)


@_setup_sig
def setup(app: Sphinx) -> dict[str, Any]:
    """Patches :mod:`sphinx_autodoc_typehints` for a more elegant display."""
    if "sphinx.ext.autodoc" not in app.extensions:
        msg = "`scanpydoc.elegant_typehints` requires `sphinx.ext.autodoc`."
        raise RuntimeError(msg)

    app.add_config_value("qualname_overrides", default={}, rebuild="html")
    app.add_config_value("annotate_defaults", default=True, rebuild="html")
    app.connect("config-inited", _init_vars)

    from ._formatting import typehints_formatter

    app.config["typehints_formatter"] = PickleableCallable(typehints_formatter)

    from ._autodoc_patch import dir_head_adder

    ClassDocumenter.add_directive_header = dir_head_adder(  # type: ignore[method-assign,assignment]
        qualname_overrides,
        ClassDocumenter.add_directive_header,
    )

    from . import _return_tuple

    _return_tuple.setup(app)

    return metadata

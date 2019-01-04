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

   And necessary since :attr:`~definition.__qualname__` does not necessarily match
   the documented location of the function/class.

   The defaults include :class:`anndata.AnnData`, :class:`pandas.DataFrame`,
   :class:`scipy.sparse.spmatrix` and other classes in :mod:`scipy.sparse`.

"""
import inspect
from collections import ChainMap
from typing import Union, Mapping, Dict, Any, Type

import sphinx_autodoc_typehints
from sphinx.application import Sphinx
from sphinx.config import Config

from . import _setup_sig, metadata


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


fa_orig = sphinx_autodoc_typehints.format_annotation


def format_annotation(annotation: Type[Any]) -> str:
    """Generate reStructuredText containing links to the types.

    Unlike :func:`sphinx_autodoc_typehints.format_annotation`,
    it tries to achieve a simpler style as seen in numeric packages like numpy.

    Args:
        annotation: A type or class used as type annotation.

    Returns:
        reStructuredText describing the type
    """
    union_params = getattr(annotation, "__union_params__", None)
    # display `Union[A, B]` as `A, B`
    if getattr(annotation, "__origin__", None) is Union or union_params:
        params = union_params or getattr(annotation, "__args__", None)
        # Never use the `Optional` keyword in the displayed docs.
        # Use the more verbose `, None` instead,
        # as is the convention in the other large numerical packages
        # if len(params or []) == 2 and getattr(params[1], '__qualname__', None) == 'NoneType':
        #     return fa_orig(annotation)  # Optional[...]
        return ", ".join(map(format_annotation, params))
    # do not show the arguments of Mapping
    if getattr(annotation, "__origin__", None) is Mapping:
        return ":class:`~typing.Mapping`"
    if inspect.isclass(annotation):
        full_name = f"{annotation.__module__}.{annotation.__qualname__}"
        override = qualname_overrides.get(full_name)
        if override is not None:
            return f":py:class:`~{override}`"
    return fa_orig(annotation)


@_setup_sig
def setup(app: Sphinx) -> Dict[str, Any]:
    """Patches :mod:`sphinx_autodoc_typehints` for a more elegant display."""
    app.add_config_value("qualname_overrides", {}, "")
    app.connect("config-inited", _init_vars)
    sphinx_autodoc_typehints.format_annotation = format_annotation

    return metadata

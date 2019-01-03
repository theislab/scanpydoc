"""Override some classnames in autodoc

This makes sure that automatically documented links actually
end up being links instead of pointing nowhere.
"""
import inspect
from typing import Union, Mapping, Dict, Any

import sphinx_autodoc_typehints
from sphinx.application import Sphinx

qualname_overrides = {
    "anndata.base.AnnData": "anndata.AnnData",
    "pandas.core.frame.DataFrame": "pandas.DataFrame",
    "scipy.sparse.base.spmatrix": "scipy.sparse.spmatrix",
    "scipy.sparse.csr.csr_matrix": "scipy.sparse.csr_matrix",
    "scipy.sparse.csc.csc_matrix": "scipy.sparse.csc_matrix",
}

fa_orig = sphinx_autodoc_typehints.format_annotation


def format_annotation(annotation):
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


def setup(app: Sphinx) -> Dict[str, Any]:
    sphinx_autodoc_typehints.format_annotation = format_annotation

    from . import metadata

    return metadata

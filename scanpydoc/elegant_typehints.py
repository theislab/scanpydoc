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
#. The config value ``annotate_defaults`` (default: :data:`True`) controls if rST code
   like ``(default: `42`)`` is added after the type.

.. _sphinx issue 4826: https://github.com/sphinx-doc/sphinx/issues/4826
.. _sphinx-autodoc-typehints issue 38: https://github.com/agronholm/sphinx-autodoc-typehints/issues/38

"""
import inspect
from collections import abc, ChainMap
from functools import partial
from pathlib import Path
from typing import Any, Union  # Meta
from typing import Type, Mapping, Sequence, Iterable  # ABC
from typing import Dict, List, Tuple  # Concrete

try:
    from typing import Literal
except ImportError:
    try:
        from typing_extensions import Literal
    except ImportError:
        Literal = object()


import sphinx_autodoc_typehints
from sphinx_autodoc_typehints import format_annotation as _format_orig
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
    "anndata.core.anndata.AnnData": "anndata.AnnData",
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


def _literal_values(origin, annotation):
    if origin is Literal:
        values = annotation.__args__
    elif hasattr(annotation, "__values__"):
        values = annotation.__values__
    else:
        return None
    return ", ".join(f"``{a!r}``" for a in values)


def _format_full(annotation: Type[Any], fully_qualified: bool = False):
    if inspect.isclass(annotation) and annotation.__module__ == "builtins":
        return _format_orig(annotation, fully_qualified)

    origin = getattr(annotation, "__origin__", None)
    tilde = "" if fully_qualified else "~"

    # Not yet supported by sphinx_autodoc_typehints
    literal_values = _literal_values(origin, annotation)
    if literal_values:
        return f":py:data:`{tilde}typing.Literal`\\[{literal_values}]"

    annotation_cls = annotation if inspect.isclass(annotation) else type(annotation)
    if annotation_cls.__module__ == "typing":
        return _format_orig(annotation, fully_qualified)

    # Only if this is a real class we override sphinx_autodoc_typehints
    if inspect.isclass(annotation) or inspect.isclass(origin):
        full_name = f"{annotation.__module__}.{annotation.__qualname__}"
        override = qualname_overrides.get(full_name)
        if override is not None:
            return f":py:class:`{tilde}{override}`"

    return _format_orig(annotation, fully_qualified)


def _format_terse(annotation: Type[Any], fully_qualified: bool = False) -> str:
    origin = getattr(annotation, "__origin__", None)

    union_params = getattr(annotation, "__union_params__", None)
    # display `Union[A, B]` as `A, B`
    if origin is Union or union_params:
        params = union_params or getattr(annotation, "__args__", None)
        # Never use the `Optional` keyword in the displayed docs.
        # Use the more verbose `, None` instead,
        # as is the convention in the other large numerical packages
        # if len(params or []) == 2 and getattr(params[1], '__qualname__', None) == 'NoneType':
        #     return fa_orig(annotation)  # Optional[...]
        return ", ".join(_format_terse(p, fully_qualified) for p in params)

    # do not show the arguments of Mapping
    if origin in (abc.Mapping, Mapping):
        return f":py:class:`{'' if fully_qualified else '~'}typing.Mapping`"

    # display dict as {k: v}
    if origin in (dict, Dict):
        k, v = annotation.__args__
        return f"{{{_format_terse(k, fully_qualified)}: {_format_terse(v, fully_qualified)}}}"

    literal_values = _literal_values(origin, annotation)
    if literal_values:
        return f"{{{literal_values}}}"

    return _format_full(annotation, fully_qualified)


def format_annotation(annotation: Type[Any], fully_qualified: bool = False) -> str:
    r"""Generate reStructuredText containing links to the types.

    Unlike :func:`sphinx_autodoc_typehints.format_annotation`,
    it tries to achieve a simpler style as seen in numeric packages like numpy.

    Args:
        annotation: A type or class used as type annotation.
        fully_qualified: If links should be formatted as fully qualified
            (e.g. ``:py:class:`foo.Bar```) or not (e.g. ``:py:class:`~foo.Bar```).

    Returns:
        reStructuredText describing the type
    """
    if sphinx_autodoc_typehints.format_annotation is not format_annotation:
        raise RuntimeError(
            "This function is not guaranteed to work correctly without overriding"
            "`sphinx_autodoc_typehints.format_annotation` with it."
        )

    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    if calframe[1][3] == "process_docstring":
        annot_fmt = (
            f":annotation-terse:`{_escape(_format_terse(annotation, fully_qualified))}`\\ "
            f":annotation-full:`{_escape(_format_full(annotation, fully_qualified))}`"
        )
        if annotate_defaults:
            variables = calframe[1].frame.f_locals
            sig = inspect.signature(variables["obj"])
            if variables["argname"] != "return":
                default = sig.parameters[variables["argname"]].default
                if default is not inspect.Parameter.empty:
                    annot_fmt += f" (default: ``{_escape(repr(default))}``)"
        return annot_fmt
    else:  # recursive use
        return _format_full(annotation, fully_qualified)


def _role_annot(
    name: str,
    rawtext: str,
    text: str,
    lineno: int,
    inliner: Inliner,
    options: Dict[str, Any] = {},
    content: Sequence[str] = (),
    # *,  # https://github.com/ambv/black/issues/613
    additional_classes: Iterable[str] = (),
) -> Tuple[List[Node], List[SystemMessage]]:
    options = options.copy()
    set_classes(options)
    if additional_classes:
        options["classes"] = options.get("classes", []).copy()
        options["classes"].extend(additional_classes)
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
    # TODO: Unsure if “html” is sufficient or if we need to do “env”;
    #       Depends on when the autodoc-process-docstring event is handled.
    app.add_config_value("qualname_overrides", {}, "html")
    app.add_config_value("annotate_defaults", True, "html")
    app.add_css_file("typehints.css")
    app.connect("config-inited", _init_vars)
    sphinx_autodoc_typehints.format_annotation = format_annotation
    for name in ["annotation-terse", "annotation-full"]:
        roles.register_canonical_role(
            name, partial(_role_annot, additional_classes=name.split("-"))
        )

    return metadata

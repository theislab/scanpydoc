"""Generate autosummary docs for imported members.

This extension patches the :mod:`~sphinx.ext.autosummary` extension
to generate docs for imported members.
It needs to be loaded and :confval:`autosummary_generate` needs to be set to ``True``.

This will hopefully be superseded by the ability to add ``:imported-members:``
to `autosummary templates`_ in the future. See `Sphinx issue 4372`_.

.. _autosummary templates: http://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html#customizing-templates
.. _Sphinx issue 4372: https://github.com/sphinx-doc/sphinx/issues/4372
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from pathlib import Path

from sphinx.ext import autosummary
from sphinx.ext.autosummary.generate import generate_autosummary_docs

from . import metadata, _setup_sig


if TYPE_CHECKING:
    from sphinx.application import Sphinx


logger = logging.getLogger(__name__)


def _generate_stubs(app: Sphinx) -> None:
    gen_files = app.config.autosummary_generate

    if gen_files and not hasattr(gen_files, "__len__"):
        env = app.builder.env
        gen_files = [
            env.doc2path(x, base=False)
            for x in env.found_docs
            if Path(env.doc2path(x)).is_file()
        ]
    if not gen_files:
        return

    ext = app.config.source_suffix
    gen_files = [
        genfile + ("" if genfile.endswith(tuple(ext)) else ext[0])
        for genfile in gen_files
    ]

    suffix = autosummary.get_rst_suffix(app)
    if suffix is None:
        return

    generate_autosummary_docs(
        gen_files,
        suffix=suffix,
        base_path=app.srcdir,
        imported_members=True,
        app=app,
    )


@_setup_sig
def setup(_app: Sphinx) -> dict[str, Any]:
    """Patch autosummary to generate docs for imported members as well."""
    autosummary.process_generate_options = _generate_stubs

    return metadata

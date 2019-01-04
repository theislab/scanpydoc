# -*- coding: future-fstrings -*-
"""Generate autosummary docs for imported members

Patches :mod:`~sphinx.ext.autosummary` to generate docs for imported members.

This will hopefully be superseded by the ability to add ``:imported-members:``
to `autosummary templates`_ in te future. See `Sphinx issue 4372`_.

.. _autosummary templates: http://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html#customizing-templates
.. _Sphinx issue 4372: https://github.com/sphinx-doc/sphinx/issues/4372
"""

import logging
from pathlib import Path
from typing import Dict, Any

from sphinx.application import Sphinx
from sphinx.ext import autosummary
from sphinx.ext.autosummary.generate import generate_autosummary_docs

from . import _setup_sig, metadata


logger = logging.getLogger(__name__)


def process_generate_options(app: Sphinx):
    genfiles = app.config.autosummary_generate

    if genfiles and not hasattr(genfiles, "__len__"):
        env = app.builder.env
        genfiles = [
            env.doc2path(x, base=None)
            for x in env.found_docs
            if Path(env.doc2path(x)).is_file()
        ]
    if not genfiles:
        return

    ext = app.config.source_suffix
    genfiles = [
        genfile + ("" if genfile.endswith(tuple(ext)) else ext[0])
        for genfile in genfiles
    ]

    suffix = autosummary.get_rst_suffix(app)
    if suffix is None:
        return

    generate_autosummary_docs(
        genfiles,
        builder=app.builder,
        warn=logger.warning,
        info=logger.info,
        suffix=suffix,
        base_path=app.srcdir,
        imported_members=True,
        app=app,
    )


@_setup_sig
def setup(app: Sphinx) -> Dict[str, Any]:
    """Patch autosummary to generate docs for imported members as well"""
    autosummary.process_generate_options = process_generate_options

    return metadata

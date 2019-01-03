# -*- coding: future-fstrings -*-
"""Generate autosummary docs for imported members

Patches autosummary to generate docs for imported members
"""

import logging
from pathlib import Path
from typing import Dict, Any

from sphinx.application import Sphinx
from sphinx.ext import autosummary
from sphinx.ext.autosummary.generate import generate_autosummary_docs


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


def setup(app: Sphinx) -> Dict[str, Any]:
    autosummary.process_generate_options = process_generate_options

    from . import metadata

    return metadata

# -*- coding: future-fstrings -*-
"""A series of Sphinx extensions to get easy to maintain, numpydoc style documentation.
"""

from typing import Any, Dict

from get_version import get_version
from sphinx.application import Sphinx


__version__ = get_version(__file__)

metadata = dict(version=__version__, env_version=1, parallel_read_safe=True)


def setup(app: Sphinx) -> Dict[str, Any]:
    from . import (
        autosummary_generate_imported,
        definition_list_typed_field,
        elegant_typehints,
        rtd_github_links,
    )

    autosummary_generate_imported.setup(app)
    definition_list_typed_field.setup(app)
    elegant_typehints.setup(app)
    rtd_github_links.setup(app)

    return metadata

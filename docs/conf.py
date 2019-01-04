import sys
from datetime import datetime
from pathlib import Path

from sphinx.application import Sphinx

# Allow importing scanpydoc itself
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import scanpydoc  # noqa


needs_sphinx = "1.7"  # autosummary bugfix
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",  # needs to be after napoleon
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "scanpydoc",
]

intersphinx_mapping = dict(
    jinja=("http://jinja.pocoo.org/docs/2.10", None),
    python=("https://docs.python.org/3", None),
    sphinx=("https://www.sphinx-doc.org/en/master/", None),
)

# general information
project = scanpydoc.__name__
author = "Philipp Angerer"
copyright = f"{datetime.now():%Y}, {author}."
version = release = scanpydoc.__version__

master_doc = "index"
templates_path = ["_templates"]

# Generate .rst stubs for modules using autosummary
autosummary_generate = True
# Don’t add module paths to documented functions’ names
add_module_names = False

html_context = dict(
    github_user="theislab", github_repo="scanpydoc", github_version="master"
)

# proj/doc/conf.py/../.. → proj
project_dir = Path(__file__).parent.parent


def setup(app: Sphinx):
    app.add_object_type(
        "confval",
        "confval",
        objname="configuration value",
        indextemplate="pair: %s; configuration value",
    )

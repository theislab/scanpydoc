from pathlib import Path

from sphinx.application import Sphinx


needs_sphinx = "1.7"  # autosummary bugfix
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",  # needs to be after napoleon
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
]

intersphinx_mapping = dict(
    jinja=("http://jinja.pocoo.org/docs/2.10", None),
    python=("https://docs.python.org/3", None),
)

autosummary_generate = True

templates_path = ["_templates"]
master_doc = "index"

html_context = dict(
    github_user="theislab", github_repo="scanpydoc", github_version="master"
)

# proj/doc/conf.py/../.. → proj
project_dir = Path(__file__).parent.parent


def setup(app: Sphinx):
    from scanpydoc import setup

    setup(app)

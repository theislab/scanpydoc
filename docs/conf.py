import sys
from datetime import datetime
from importlib.metadata import metadata
from pathlib import Path

from sphinx.application import Sphinx


HERE = Path(__file__).parent

# necessary for rtd_gh_links’ linkcode support
sys.path.insert(0, HERE.parent / "src")

# Clean build env
for file in HERE.glob("scanpydoc.*.rst"):
    file.unlink()

extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",  # needs to be after napoleon
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "scanpydoc",
    "sphinx.ext.linkcode",  # needs to be after scanpydoc
]

intersphinx_mapping = dict(
    python=("https://docs.python.org/3", None),
    jinja=("https://jinja.palletsprojects.com/en/2.10.x/", None),
    sphinx=("https://www.sphinx-doc.org/en/master/", None),
    sphinx_book_theme=("https://sphinx-book-theme.readthedocs.io/en/stable/", None),
    # examples
    numpy=("https://numpy.org/doc/stable/", None),
    anndata=("https://anndata.readthedocs.io/en/latest/", None),
    pandas=("https://pandas.pydata.org/pandas-docs/stable/", None),
    scipy=("https://docs.scipy.org/doc/scipy/", None),
)

# general information
meta = metadata("scanpydoc")
project = meta["name"]
author = meta["author-email"].split(" <")[0]
copyright = f"{datetime.now():%Y}, {author}."
version = release = meta["version"]

master_doc = "index"
templates_path = ["_templates"]

# Generate .rst stubs for modules using autosummary
autosummary_generate = True
# Don’t add module paths to documented functions’ names
add_module_names = False

html_theme = "scanpydoc"
html_context = dict(
    repository_url="https://github.com/theislab/scanpydoc",
    repository_branch="main",
    use_repository_button=True,
)

rtd_links_prefix = "src"


def setup(app: Sphinx):
    app.add_object_type(
        "confval",
        "confval",
        objname="configuration value",
        indextemplate="pair: %s; configuration value",
    )

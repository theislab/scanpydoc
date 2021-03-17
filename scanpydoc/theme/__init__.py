"""A widescreen extension for :doc:`sphinx_rtd_theme:index`.

Add to ``conf.py``:

.. code:: python

   html_theme = 'scanpydoc'

Theme options
=============

This theme adds the following configuration option,
and the ones under `docsearch options`_:

.. confval:: accent_color

   :type: str
   :default: ``#f07e44``

   The CSS color used for the mobile header background and the project name text.

See ``sphinx_rtd_theme``’s :doc:`sphinx_rtd_theme:configuring`, e.g.:

.. code:: python

   html_theme_options = dict(
       logo_only=False,
       accent_color='rebeccapurple',
       display_version=False,
   )

Docsearch options
-----------------

These two configuration values are required to use docsearch_:

.. _docsearch: https://docsearch.algolia.com/

.. confval:: docsearch_key

   :type: str

   The API key provided by docsearch.

.. confval:: docsearch_index

   :type: str

   The index name used by docsearch.

The following configuration values are optional:

.. confval:: docsearch_doc_version

   :type: str
   :default: ``'latest'`` or ``'stable'``

   The documentation version searched.
   The default is ``'stable'`` if ``READTHEDOCS_VERSION=stable`` is set,
   and ``'latest'`` otherwise.

.. confval:: docsearch_js_version

   :type: str
   :default: ``'2.6'``

   The docsearch library version used.

"""

from pathlib import Path

from sphinx.application import Sphinx

from .. import _setup_sig


HERE = Path(__file__).parent.resolve()


@_setup_sig
def setup(app: Sphinx):
    """Setup theme (like an extension)"""
    app.add_html_theme("scanpydoc", str(HERE))
    return dict(parallel_read_safe=True, parallel_write_safe=True)

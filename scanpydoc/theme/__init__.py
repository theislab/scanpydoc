"""A widescreen extension for :doc:`sphinx_rtd_theme:index`.

Add to ``conf.py``:

.. code:: python

   html_theme = 'scanpydoc'

Theme options
=============

This theme only adds one configuration value:

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

scanpydoc |pypi| |docs| |tests| |checks| |cov|
==============================================

.. attention::

    This package is deprecated. Use scverse-doc_ instead:

    .. list-table::
       :header-rows: 1

       * - scanpydoc extension
         - scverse-doc replacement
       * - ``scanpydoc``
         - ``extensions = ["scverse_doc"]``
       * - ``scanpydoc.definition_list_typed_field``
         - ``scverse_doc.typed_fields``
       * - ``scanpydoc.elegant_typehints``
         - ``scverse_doc.xref_overrides`` (``qualname_overrides`` → ``xref_overrides``)
           and ``scverse_doc.napoleon``
       * - ``scanpydoc.rtd_github_links``
         - ``scverse_doc.source`` (with ``source_repository = ...``)
       * - ``scanpydoc.theme``
         - ``html_theme = "scverse"``
       * - ``scanpydoc.release_notes``
         - ``scverse_doc.release_notes``

.. _scverse-doc: https://github.com/scverse/scverse-doc

A collection of Sphinx extensions similar to (but more flexible than) numpydoc.

Check the self-documenting documentation at https://icb-scanpydoc.readthedocs-hosted.com

.. |pypi| image:: https://img.shields.io/pypi/v/scanpydoc.svg
   :target: https://pypi.org/project/scanpydoc/
   :alt: PiPI version
.. |docs| image:: https://readthedocs.com/projects/icb-scanpydoc/badge/
   :target: https://icb-scanpydoc.readthedocs-hosted.com/
   :alt: doc build status
.. |tests| image:: https://github.com/theislab/scanpydoc/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/theislab/scanpydoc/actions/workflows/ci.yml
   :alt: python test status
.. |checks| image:: https://results.pre-commit.ci/badge/github/theislab/scanpydoc/main.svg
   :target: https://results.pre-commit.ci/latest/github/theislab/scanpydoc/main
   :alt: pre-commit.ci status
.. |cov| image:: https://codecov.io/gh/theislab/scanpydoc/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/theislab/scanpydoc
   :alt: coverage

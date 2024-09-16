"""A release notes directive.

Given a list of version files matching :attr:`FULL_VERSION_RE`,
render them using the following (where ``.`` is the directory they are in):

.. code:: restructuredtext

    .. release-notes:: .

With e.g. the files :file:`1.2.0.md`, :file:`1.2.1.md`, and :file:`1.3.0.rst`,
this will render like the following:

.. code:: restructuredtext

   _v1.3:

   Version 1.3
   ===========

   .. include:: 1.3.0.rst


   _v1.2:

   Version 1.2
   ===========

   .. include:: 1.2.1.md
   .. include:: 1.2.0.md
"""

from __future__ import annotations

import re
import itertools
from typing import TYPE_CHECKING
from pathlib import Path
from dataclasses import dataclass

from docutils import nodes
from packaging.version import Version
from sphinx.util.parsing import nested_parse_to_nodes
from sphinx.util.docutils import SphinxDirective

from . import metadata, _setup_sig


if TYPE_CHECKING:
    from typing import Any, ClassVar
    from collections.abc import Iterable, Sequence

    from sphinx.application import Sphinx
    from myst_parser.mdit_to_docutils.base import DocutilsRenderer


FULL_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:.*)?$")
"""Regex matching a full version number including patch part, maybe with more after."""


@dataclass
class _Backend:
    dir: Path
    instance: SphinxDirective

    def run(self) -> Sequence[nodes.Node]:
        versions = sorted(
            (
                (Version(f.stem), f)
                for f in self.dir.iterdir()
                if FULL_VERSION_RE.match(f.stem)
            ),
            reverse=True,  # descending
        )
        version_groups = itertools.groupby(
            versions, key=lambda vf: (vf[0].major, vf[0].minor)
        )
        return [
            node
            for (major, minor), versions in version_groups
            for node in self.render_version_group(major, minor, versions)
        ]

    def render_version_group(
        self,
        major: int,
        minor: int,
        versions: Iterable[tuple[Version, Path]] = (),
    ) -> tuple[nodes.target, nodes.section]:
        target = nodes.target(
            ids=[f"v{major}-{minor}"],
            names=[f"v{major}.{minor}"],
        )
        section = nodes.section(
            "",
            nodes.title("", f"Version {major}.{minor}"),
            ids=[],
            names=[f"version {major}.{minor}"],
        )

        self.instance.state.document.note_implicit_target(section)
        self.instance.state.document.note_explicit_target(target)

        for _, p in versions:
            section += self.render_include(p)
        return target, section

    def render_include(self, path: Path) -> Sequence[nodes.Node]:
        return nested_parse_to_nodes(
            self.instance.state,
            path.read_text(),
            source=str(path),
            offset=self.instance.content_offset,
        )


# TODO(flying-sheep): Remove once MyST-Parser bug is fixed
# https://github.com/executablebooks/MyST-Parser/issues/967
class _BackendMyst(_Backend):
    def run(self) -> Sequence[nodes.Node]:
        super().run()
        return []

    def render_version_group(
        self, major: int, minor: int, versions: Iterable[tuple[Version, Path]] = ()
    ) -> tuple[nodes.target, nodes.section]:
        target, section = super().render_version_group(major, minor)
        # append target and section to parent
        self._myst_renderer.current_node.append(target)
        self._myst_renderer.update_section_level_state(section, 2)
        # append children to section
        for _, p in versions:
            with self._myst_renderer.current_node_context(section):
                self.render_include(p)
        return target, section  # ignored, just to not change the types

    def render_include(self, path: Path) -> Sequence[nodes.Node]:
        from myst_parser.mocking import MockIncludeDirective
        from docutils.parsers.rst.directives.misc import Include

        srcfile, lineno = self.instance.get_source_info()
        parent_dir = Path(srcfile).parent

        d = MockIncludeDirective(
            renderer=self._myst_renderer,
            name=type(self).__name__,
            klass=Include,  # type: ignore[arg-type]  # wrong type hint
            arguments=[str(path.relative_to(parent_dir))],
            options={},
            body=[],
            lineno=lineno,
        )
        return d.run()

    @property
    def _myst_renderer(self) -> DocutilsRenderer:
        rv: DocutilsRenderer = self.instance.state._renderer  # type: ignore[attr-defined]  # noqa: SLF001
        return rv


class ReleaseNotes(SphinxDirective):
    """Directive rendering release notes, grouping them by minor versions."""

    required_arguments: ClassVar = 1

    def run(self) -> Sequence[nodes.Node]:
        """Read the release notes and render them."""
        dir_ = Path(self.arguments[0])
        # resolve relative dir
        if not dir_.is_absolute():
            src_file = Path(self.get_source_info()[0])
            if not src_file.is_file():
                msg = f"Cannot find relative path to: {src_file}"
                raise self.error(msg)
            dir_ = src_file.parent / self.arguments[0]
        if not dir_.is_dir():
            msg = f"Not a directory: {dir_}"
            raise self.error(msg)

        cls = _BackendMyst if hasattr(self.state, "_renderer") else _Backend
        return cls(dir_, self).run()


@_setup_sig
def setup(app: Sphinx) -> dict[str, Any]:
    """Add the ``release-notes`` directive."""
    app.add_directive("release-notes", ReleaseNotes)
    return metadata

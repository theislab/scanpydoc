from __future__ import annotations

from typing import TYPE_CHECKING
from functools import wraps


if TYPE_CHECKING:
    from collections.abc import Mapping, Callable

    from sphinx.ext.autodoc import ClassDocumenter
    from docutils.statemachine import StringList


def dir_head_adder(
    qualname_overrides: Mapping[tuple[str | None, str], tuple[str | None, str]],
    orig: Callable[[ClassDocumenter, str], None],
) -> Callable[[ClassDocumenter, str], None]:
    @wraps(orig)
    def add_directive_header(self: ClassDocumenter, sig: str) -> None:
        orig(self, sig)
        lines = self.directive.result
        inferred_role, direc = (
            ("py:exc", "py:exception")
            if isinstance(self.object, type) and issubclass(self.object, BaseException)
            else ("py:class", "py:class")
        )
        for (old_role, old_name), (new_role, new_name) in qualname_overrides.items():
            role = inferred_role if new_role is None else new_role
            # Currently, autodoc doesn’t link to bases using :exc:
            lines.replace(
                f":{old_role or 'py:class'}:`{old_name}`", f":{role}:`{new_name}`"
            )
            # But maybe in the future it will
            lines.replace(f":{role}:`{old_name}`", f":{role}:`{new_name}`")
            old_mod, old_cls = old_name.rsplit(".", 1)
            new_mod, new_cls = new_name.rsplit(".", 1)
            replace_multi_suffix(
                lines,
                (f".. {direc}:: {old_cls}", f"   :module: {old_mod}"),
                (f".. {direc}:: {new_cls}", f"   :module: {new_mod}"),
            )

    return add_directive_header


def replace_multi_suffix(
    lines: StringList, old: tuple[str, str], new: tuple[str, str]
) -> None:
    if len(old) != len(new) != 2:  # noqa: PLR2004  # pragma: no cover
        msg = "Only supports replacing 2 lines"
        raise NotImplementedError(msg)
    for l, line in enumerate(lines):
        start = line.find(old[0])
        if start == -1:
            continue
        prefix = line[:start]
        suffix = line[start + len(old[0]) :]
        if lines[l + 1].startswith(prefix + old[1]):
            break
    else:
        return
    lines[l + 0] = prefix + new[0] + suffix
    lines[l + 1] = prefix + new[1]

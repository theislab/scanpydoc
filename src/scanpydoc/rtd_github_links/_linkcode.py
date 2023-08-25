from __future__ import annotations

from typing import Literal, TypedDict


class PyInfo(TypedDict):
    module: str
    fullname: str


class CInfo(TypedDict):
    """C / C++ info."""

    names: list[str]


class JSInfo(TypedDict):
    object: str
    fullname: str


def linkcode_resolve(
    domain: Literal["py", "c", "cpp", "javascript"],
    info: PyInfo | CInfo | JSInfo,
) -> str | None:
    from . import github_url

    if domain != "py":
        return None
    if not info["module"]:
        return None
    return github_url(f'{info["module"]}.{info["fullname"]}')

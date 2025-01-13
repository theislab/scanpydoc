from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, cast, overload


class PyInfo(TypedDict):
    module: str
    fullname: str


class CInfo(TypedDict):
    """C / C++ info."""

    names: list[str]


class JSInfo(TypedDict):
    object: str
    fullname: str


if TYPE_CHECKING:
    from typing import Literal, TypeAlias

    Domain = Literal["py", "c", "cpp", "javascript"]
    DomainInfo: TypeAlias = PyInfo | CInfo | JSInfo


@overload
def linkcode_resolve(
    domain: Literal["py"], info: PyInfo
) -> str | None:  # pragma: no cover
    ...


@overload
def linkcode_resolve(
    domain: Literal["c", "cpp"], info: CInfo
) -> str | None:  # pragma: no cover
    ...


@overload
def linkcode_resolve(
    domain: Literal["javascript"], info: JSInfo
) -> str | None:  # pragma: no cover
    ...


def linkcode_resolve(domain: Domain, info: DomainInfo) -> str | None:
    from . import github_url

    if domain != "py":
        return None
    info = cast(PyInfo, info)
    if not info["module"]:
        return None
    return github_url(f"{info['module']}.{info['fullname']}")

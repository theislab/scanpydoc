"""This module exists just for rtd_github_links tests."""  # noqa: D404

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar
from dataclasses import field, dataclass

from legacy_api_wrap import legacy_api


if TYPE_CHECKING:
    from typing import TypeAlias


_T = TypeVar("_T")


class _G(Generic[_T]):
    pass


# make sure that TestGenericClass keeps its __module__
_G.__module__ = "somewhere_else"


TestGenericBuiltin: TypeAlias = list[str]
TestGenericClass: TypeAlias = _G[int]


@dataclass
class TestDataCls:
    test_attr: dict[str, str] = field(default_factory=dict)


class TestCls:
    test_anno: int


def test_func() -> None:  # pragma: no cover
    pass


@legacy_api()
def test_func_wrap() -> None:  # pragma: no cover
    pass

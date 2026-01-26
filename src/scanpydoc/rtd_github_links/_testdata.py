"""This module exists just for rtd_github_links tests."""  # noqa: D404

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar
from dataclasses import field, dataclass

from legacy_api_wrap import legacy_api


if TYPE_CHECKING:
    from typing import TypeAlias


class _G[T]:
    pass


_T = TypeVar("_T")


class _G_Old(Generic[_T]):  # noqa: N801, UP046
    pass


# make sure that TestGenericClass keeps its __module__
_G.__module__ = _G_Old.__module__ = "somewhere_else"


type TestGenericBuiltin = list[str]
type TestGenericClass = _G[int]
TestGenericBuiltinOld: TypeAlias = list[str]  # noqa: UP040
TestGenericClassOld: TypeAlias = _G_Old[int]  # noqa: UP040


@dataclass
class TestDataCls:
    test_attr: dict[str, str] = field(default_factory=dict)


class TestCls:
    test_anno: int


# make sure annotations are picked up from supertypes
class TestClsChild(TestCls): ...


def test_func() -> None:  # pragma: no cover
    pass


@legacy_api()
def test_func_wrap() -> None:  # pragma: no cover
    pass

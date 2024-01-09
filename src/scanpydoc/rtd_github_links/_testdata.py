"""This module exists just for rtd_github_links tests."""  # noqa: D404

from __future__ import annotations

from dataclasses import field, dataclass

from legacy_api_wrap import legacy_api


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

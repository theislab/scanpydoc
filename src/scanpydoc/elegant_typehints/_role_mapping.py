from __future__ import annotations

from typing import TYPE_CHECKING
from itertools import chain
from collections.abc import MutableMapping


if TYPE_CHECKING:
    from typing import Self
    from collections.abc import Mapping, Iterator


class RoleMapping(MutableMapping[tuple[str | None, str], tuple[str | None, str]]):
    data: dict[tuple[str | None, str], tuple[str | None, str]]

    def __init__(
        self,
        mapping: Mapping[tuple[str | None, str], str | tuple[str | None, str]] = {},
        /,
    ) -> None:
        self.data = dict(mapping)  # type: ignore[arg-type]

    @classmethod
    def from_user(
        cls, mapping: Mapping[str | tuple[str, str], str | tuple[str, str]]
    ) -> Self:
        rm = cls({})
        rm.update_user(mapping)
        return rm

    def update_user(
        self, mapping: Mapping[str | tuple[str, str], str | tuple[str, str]]
    ) -> None:
        for k, v in mapping.items():
            self[k if isinstance(k, tuple) else (None, k)] = (
                v if isinstance(v, tuple) else (None, v)
            )

    def __setitem__(
        self, key: tuple[str | None, str], value: tuple[str | None, str]
    ) -> None:
        self.data[key] = value

    def __getitem__(self, key: tuple[str | None, str]) -> tuple[str | None, str]:
        if key[0] is not None:
            try:
                return self.data[key]
            except KeyError:
                return self.data[None, key[1]]
        for known_role in chain([None], {r for r, _ in self}):
            try:
                return self.data[known_role, key[1]]
            except KeyError:  # noqa: PERF203
                pass
        raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, tuple):
            raise TypeError
        try:
            self[key]
        except KeyError:
            return False
        return True

    def __delitem__(self, key: tuple[str | None, str]) -> None:
        del self.data[key]

    def __iter__(self) -> Iterator[tuple[str | None, str]]:
        return self.data.__iter__()

    def __len__(self) -> int:
        return len(self.data)

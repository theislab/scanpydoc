from __future__ import annotations


def example_func_prose(
    a: str | None, b: str | int | None = None
) -> dict[str, int]:  # pragma: no cover
    """Example function with a paragraph return section.

    Parameters
    ----------
    a
        An example parameter
    b
        Another, with a default

    Returns
    -------
    An example dict
    """
    return {}


def example_func_tuple() -> tuple[int, str]:  # pragma: no cover
    """Example function with return tuple.

    Returns
    -------
    x
        An example int
    y
        An example str
    """
    return (1, "foo")


def example_func_anonymous_tuple() -> tuple[int, str]:  # pragma: no cover
    """Example function with anonymous return tuple.

    Returns
    -------
    :
        An example int
    :
        An example str
    """
    return (1, "foo")

"""Test elegant_typehints subextension."""

from __future__ import annotations

import re
import sys
import inspect
from io import StringIO
from typing import (
    TYPE_CHECKING,
    Any,
    Union,
    AnyStr,
    NoReturn,
    Optional,
    cast,
    get_origin,
)
from pathlib import Path
from textwrap import dedent
from collections.abc import Mapping, Callable

import pytest
import sphinx_autodoc_typehints as sat
from sphinx.errors import ExtensionError

from scanpydoc.elegant_typehints._formatting import typehints_formatter
from scanpydoc.elegant_typehints._return_tuple import process_docstring


if TYPE_CHECKING:
    from types import ModuleType

    from sphinx.application import Sphinx


NONE_RTYPE = ":rtype: :sphinx_autodoc_typehints_type:`\\:py\\:obj\\:\\`None\\``"


@pytest.fixture()
def testmod(make_module: Callable[[str, str], ModuleType]) -> ModuleType:
    return make_module(
        "testmod",
        """\
        class Class: pass
        class SubCl(Class): pass
        class Excep(RuntimeError): pass
        class Excep2(Excep): pass
        """,
    )


@pytest.fixture()
def app(make_app_setup: Callable[..., Sphinx]) -> Sphinx:
    return make_app_setup(
        master_doc="index",
        extensions=[
            "sphinx.ext.autodoc",
            "sphinx.ext.napoleon",
            "sphinx_autodoc_typehints",
            "scanpydoc.elegant_typehints",
        ],
        qualname_overrides={
            "testmod.Class": "test.Class",
            "testmod.SubCl": "test.SubCl",
            "testmod.Excep": "test.Excep",
            "testmod.Excep2": "test.Excep2",
        },
    )


@pytest.fixture()
def process_doc(app: Sphinx) -> Callable[[Callable[..., Any]], list[str]]:
    def process(fn: Callable[..., Any]) -> list[str]:
        lines = (inspect.getdoc(fn) or "").split("\n")
        if isinstance(fn, property):
            name = fn.fget.__name__
        elif hasattr(fn, "__name__"):
            name = fn.__name__
        else:
            name = "???"
        sat.process_docstring(app, "function", name, fn, None, lines)
        process_docstring(app, "function", name, fn, None, lines)
        return lines

    return process


def test_app(app: Sphinx) -> None:
    assert "qualname_overrides" in app.config.values
    assert "testmod.Class" in app.config.qualname_overrides


def test_default(app: Sphinx) -> None:
    assert typehints_formatter(str, app.config) is None


def _escape_sat(rst: str) -> str:
    rst = (
        rst.replace("\\", r"\\")
        .replace("`", r"\`")
        .replace(":", r"\:")
        .replace("~", r"\~")
        .replace(",", r"\,")
        .replace("[", r"\[")
        .replace("]", r"\]")
    )
    return f":sphinx_autodoc_typehints_type:`{rst}`"


@pytest.mark.parametrize(
    ("kind", "add_rtype"),
    [
        pytest.param(lambda f: f, True, id="function"),
        pytest.param(property, False, id="property"),
    ],
)
def test_kinds(
    *,
    process_doc: Callable[[Callable[..., Any]], list[str]],
    kind: Callable[[Callable[..., Any]], Callable[..., Any]],
    add_rtype: bool,
) -> None:
    def fn_test(s: str) -> None:  # pragma: no cover
        """:param s: Test"""
        del s

    assert process_doc(kind(fn_test)) == [
        f":type s: {_escape_sat(':py:class:`str`')}",
        ":param s: Test",
        *([NONE_RTYPE] if add_rtype else []),
    ]


class CustomCls:  # noqa: D101
    __slots__ = ["foo"]

    def meth(self):  # pragma: no cover  # noqa: ANN201
        """No return section and no return annotation."""


@pytest.mark.parametrize(
    "obj",
    [
        pytest.param(None, id="none"),
        pytest.param(CustomCls.foo, id="slotwrapper"),  # type: ignore[attr-defined]
        pytest.param(lambda: None, id="lambda"),
        pytest.param(CustomCls.meth, id="func_nodoc"),
        pytest.param(CustomCls().meth, id="meth_nodoc"),
    ],
)
def test_skip(
    process_doc: Callable[[Callable[..., Any]], list[str]], obj: Callable[..., Any]
) -> None:
    doc = inspect.getdoc(obj)
    assert process_doc(obj) == [doc or ""]


def test_defaults_simple(
    process_doc: Callable[[Callable[..., Any]], list[str]],
) -> None:
    def fn_test(
        s: str = "foo", n: None = None, i_: int = 1
    ) -> None:  # pragma: no cover
        r""":param s: Test S
        :param n: Test N
        :param i\_: Test I
        """  # noqa: D205
        del s, n, i_

    assert process_doc(fn_test) == [
        f":type s: {_escape_sat(':py:class:`str`')} (default: ``'foo'``)",
        ":param s: Test S",
        f":type n: {_escape_sat(':py:obj:`None`')} (default: ``None``)",
        ":param n: Test N",
        rf":type i\_: {_escape_sat(':py:class:`int`')} (default: ``1``)",
        r":param i\_: Test I",
        NONE_RTYPE,
    ]


def test_defaults_complex(
    process_doc: Callable[[Callable[..., Any]], list[str]],
) -> None:
    def fn_test(m: Mapping[str, int] = {}) -> None:  # pragma: no cover
        """:param m: Test M"""
        del m

    expected = (
        r":py:class:`~collections.abc.Mapping`\ \[:py:class:`str`, :py:class:`int`]"
    )
    assert process_doc(fn_test) == [
        f":type m: {_escape_sat(expected)} (default: ``{{}}``)",
        ":param m: Test M",
        NONE_RTYPE,
    ]


def test_qualname_overrides_class(app: Sphinx, testmod: ModuleType) -> None:
    assert testmod.Class.__module__ == "testmod"
    assert typehints_formatter(testmod.Class, app.config) == ":py:class:`~test.Class`"


def test_qualname_overrides_exception(app: Sphinx, testmod: ModuleType) -> None:
    assert testmod.Excep.__module__ == "testmod"
    assert typehints_formatter(testmod.Excep, app.config) == ":py:exc:`~test.Excep`"


# These guys aren’t listed as classes in Python’s intersphinx index:
@pytest.mark.parametrize(
    "annotation",
    [
        Any,
        AnyStr,
        NoReturn,
        Callable[[int], None],
        Union[int, str],
        Union[int, str, None],
    ],
    ids=lambda p: str(p).replace("typing.", ""),
)
def test_typing_classes(app: Sphinx, annotation: type) -> None:
    app.config.typehints_fully_qualified = True  # type: ignore[attr-defined]
    name = (
        getattr(annotation, "_name", None)
        or getattr(annotation, "__name__", None)
        or getattr(get_origin(annotation), "_name", None)
        # 3.6 _Any and _Union
        or annotation.__class__.__name__[1:]
    )
    output = typehints_formatter(annotation, app.config)
    assert output is None or output.startswith(f":py:data:`typing.{name}")


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+")
def test_union_type(app: Sphinx) -> None:
    union = eval("int | str")  # noqa: S307, PGH001
    assert typehints_formatter(union, app.config) is None


@pytest.mark.parametrize(
    ("direc", "base", "sub"),
    [
        ("autoclass", "Class", "SubCl"),
        ("autoexception", "Excep", "Excep2"),
    ],
)
def test_autodoc(
    app: Sphinx,
    testmod: ModuleType,  # noqa: ARG001
    direc: str,
    base: str,
    sub: str,
) -> None:
    Path(app.srcdir, "index.rst").write_text(
        f"""\
.. {direc}:: testmod.{sub}
   :show-inheritance:
""",
    )
    app.build()
    out = Path(app.outdir, "index.html").read_text()
    assert not (ws := cast(StringIO, app._warning).getvalue()), ws  # noqa: SLF001
    assert re.search(
        r'<(code|span)?[^>]*><span class="pre">test\.</span></(code|span)>'
        f'<(code|span)?[^>]*><span class="pre">{sub}</span></(code|span)>',
        out,
    ), out
    assert f'<a class="headerlink" href="#test.{sub}"' in out, out
    assert re.search(rf"Bases: <code[^>]*><span[^>]*>(?:test\.)?{base}", out), out


def test_fwd_ref(app: Sphinx, make_module: Callable[[str, str], ModuleType]) -> None:
    make_module(
        "fwd_mod",
        """\
        from dataclasses import dataclass

        @dataclass
        class A:
           b: 'B'

        @dataclass
        class B:
            a: A
        """,
    )
    Path(app.srcdir, "index.rst").write_text(
        """\
.. autosummary::

   fwd_mod.A
   fwd_mod.B
""",
    )
    app.setup_extension("sphinx.ext.autosummary")

    app.build()

    out = Path(app.outdir, "index.html").read_text()
    buf = cast(StringIO, app._warning)  # noqa: SLF001
    warnings = [
        w
        for w in buf.getvalue().splitlines()
        if "Cannot treat a function defined as a local function" not in w
    ]
    assert not warnings, warnings
    # TODO(flying-sheep): actually reproduce
    # https://github.com/theislab/scanpydoc/issues/14
    assert "fwd_mod.A" in out, out


@pytest.mark.parametrize(
    "docstring",
    [
        """
        :param: x
        :return: foo
                     A foo!
                 bar
                     A bar!
        """,
        """
        :return: foo
                     A foo!
                 bar
                     A bar!
        :param: x
        """,
    ],
    ids=["Last", "First"],
)
@pytest.mark.parametrize(
    ("return_ann", "foo_rendered"),
    [
        pytest.param(tuple[str, int], ":py:class:`str`", id="tuple"),
        pytest.param(Optional[tuple[str, int]], ":py:class:`str`", id="tuple | None"),
        pytest.param(
            tuple[Mapping[str, float], int],
            r":py:class:`~collections.abc.Mapping`\ \["
            ":py:class:`str`, :py:class:`float`"
            "]",
            id="complex",
        ),
        pytest.param(Optional[int], None, id="int | None"),
    ],
)
def test_return(
    process_doc: Callable[[Callable[..., Any]], list[str]],
    docstring: str,
    return_ann: type,
    foo_rendered: str | None,
) -> None:
    def fn_test() -> None:  # pragma: no cover
        pass

    fn_test.__doc__ = docstring
    fn_test.__annotations__["return"] = return_ann
    lines = [l for l in process_doc(fn_test) if not re.match("^:(rtype|param):", l)]
    if foo_rendered is None:
        assert lines == [
            l
            for l in dedent(docstring).strip().splitlines()
            if not l.startswith(":param:")
        ]
    else:
        assert lines == [
            f":return: foo : {foo_rendered}",
            "             A foo!",
            "         bar : :py:class:`int`",
            "             A bar!",
        ]


def test_return_nodoc(process_doc: Callable[[Callable[..., Any]], list[str]]) -> None:
    def fn() -> tuple[int, str]:  # pragma: no cover
        """No return section."""
        return 1, ""

    res = process_doc(fn)
    assert len(res) == 3  # noqa: PLR2004
    assert res[0:2] == [inspect.getdoc(fn), ""]
    assert res[2].startswith(":rtype: :sphinx_autodoc_typehints_type:")


def test_load_error(make_app_setup: Callable[..., Sphinx]) -> None:
    with pytest.raises(
        ExtensionError,
        match=r"Can only use annotate_defaults.*when using sphinx-autodoc-typehints",
    ):
        make_app_setup(
            extensions=["sphinx.ext.autodoc", "scanpydoc.elegant_typehints"],
            annotate_defaults=True,
        )

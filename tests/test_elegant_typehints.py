"""Test elegant_typehints subextension."""

from __future__ import annotations

import re
import inspect
from typing import TYPE_CHECKING, Any, AnyStr, NoReturn, NamedTuple, cast, get_origin
from pathlib import Path
from operator import attrgetter
from collections.abc import Mapping, Callable
from importlib.metadata import version

import pytest
from packaging.version import Version


if TYPE_CHECKING or Version(version("sphinx")) >= Version("8.2"):
    from sphinx.util.inventory import _InventoryItem
else:

    class _InventoryItem(NamedTuple):
        project_name: str
        project_version: str
        uri: str
        display_name: str


from scanpydoc.elegant_typehints import _last_resolve, qualname_overrides
from scanpydoc.elegant_typehints._formatting import typehints_formatter


if TYPE_CHECKING:
    from io import StringIO
    from types import ModuleType
    from typing import Protocol
    from collections.abc import Generator

    from sphinx.application import Sphinx

    from scanpydoc.testing import MakeApp

    class _AppParams(NamedTuple):
        args: tuple[Any, ...]
        kwargs: dict[str, Any]

    class ProcessDoc(Protocol):  # noqa: D101
        def __call__(  # noqa: D102
            self, fn: Callable[..., Any], *, run_napoleon: bool = False
        ) -> list[str]: ...


NONE_RTYPE = ":rtype: :sphinx_autodoc_typehints_type:`\\:py\\:obj\\:\\`None\\``"


@pytest.fixture(autouse=True)
def _reset_qualname_overrides() -> Generator[None, None, None]:
    yield
    qualname_overrides.clear()


@pytest.fixture
def testmod(make_module: Callable[[str, str], ModuleType]) -> ModuleType:
    return make_module(
        "testmod",
        """\
        from __future__ import annotations
        from typing import Generic, TypeVar

        class Class: pass
        class SubCl(Class): pass
        class Excep(RuntimeError): pass
        class Excep2(Excep): pass

        class Gen[T]: pass

        _T = TypeVar('T')
        class GenOld(Generic[_T]): pass
        """,
    )


@pytest.fixture
def app(make_app_setup: MakeApp) -> Sphinx:
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
            "testmod.Excep2": ("py:exc", "test.Excep2"),
            "testmod.Gen": "test.Gen",
            "testmod.GenOld": "test.GenOld",
        },
    )


@pytest.fixture
def process_doc(app: Sphinx) -> ProcessDoc:
    listeners = sorted(
        (l for l in app.events.listeners["autodoc-process-docstring"]),
        key=attrgetter("priority"),
    )
    assert [f"{l.handler.__module__}.{l.handler.__qualname__}" for l in listeners] == [
        "sphinx.ext.napoleon._process_docstring",
        "sphinx_autodoc_typehints.process_docstring",
        "scanpydoc.elegant_typehints._return_tuple.process_docstring",
    ]

    def process(fn: Callable[..., Any], *, run_napoleon: bool = False) -> list[str]:
        app.env.prepare_settings(getattr(fn, "__name__", str(fn)))
        lines = (inspect.getdoc(fn) or "").split("\n")
        if isinstance(fn, property):
            name = fn.fget.__name__
        elif hasattr(fn, "__name__"):
            name = fn.__name__
        else:
            name = "???"
        for listener in listeners:
            if (
                not run_napoleon
                and listener.handler.__module__ == "sphinx.ext.napoleon"
            ):
                continue
            listener.handler(app, "function", name, fn, None, lines)
        return lines

    return process


def test_app(app: Sphinx) -> None:
    assert "qualname_overrides" in app.config.values
    assert "testmod.Class" in app.config.qualname_overrides


@pytest.mark.parametrize("annotation", [str, int | str], ids=["type", "union"])
def test_default(app: Sphinx, annotation: object) -> None:
    assert typehints_formatter(annotation, app.config) is None


def test_typealiastype(app: Sphinx) -> None:
    type Foo = int  # pyright: ignore[reportGeneralTypeIssues]
    assert typehints_formatter(Foo, app.config) == ":py:class:`int`"


def test_doc_ref(app: Sphinx) -> None:
    qualname_overrides[None, "foo.Bar"] = ("doc", "foo/bar")
    Bar = type("Bar", (), dict(__module__="foo"))  # noqa: N806
    assert typehints_formatter(Bar, app.config) == ":doc:`Bar <foo/bar>`"


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
    process_doc: ProcessDoc,
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
def test_skip(process_doc: ProcessDoc, obj: Callable[..., Any]) -> None:
    doc = inspect.getdoc(obj)
    assert process_doc(obj) == [doc or ""]


def test_defaults_simple(process_doc: ProcessDoc) -> None:
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


def test_defaults_complex(process_doc: ProcessDoc) -> None:
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


@pytest.mark.parametrize(
    ("get", "expected"),
    [
        pytest.param(lambda m: m.Class, ":py:class:`~test.Class`", id="class"),
        pytest.param(lambda m: m.Excep, ":py:exc:`~test.Excep`", id="exc"),
        pytest.param(
            lambda m: m.Gen[m.Class],
            r":py:class:`~test.Gen`\ \[:py:class:`~test.Class`]",
            id="generic",
        ),
        pytest.param(
            lambda m: m.GenOld[m.Class],
            r":py:class:`~test.GenOld`\ \[:py:class:`~test.Class`]",
            id="generic-old",
        ),
    ],
)
def test_qualname_overrides(
    process_doc: ProcessDoc,
    testmod: ModuleType,
    get: Callable[[ModuleType], object],
    expected: str,
) -> None:
    def fn_test(m: object) -> None:  # pragma: no cover
        """:param m: Test M"""
        del m

    fn_test.__annotations__["m"] = get(testmod)
    assert fn_test.__annotations__["m"].__module__ == "testmod"

    assert process_doc(fn_test) == [
        f":type m: {_escape_sat(expected)}",
        ":param m: Test M",
        NONE_RTYPE,
    ]


@pytest.mark.parametrize(
    ("qualname", "docname"),
    [("testmod.Class", "test.Class"), ("testmod.Excep2", "test.Excep2")],
)
def test_resolve(app: Sphinx, qualname: str, docname: str) -> None:
    """Test that qualname_overrides affects _last_resolve as expected."""
    from docutils.nodes import TextElement, reference
    from sphinx.addnodes import pending_xref
    from sphinx.ext.intersphinx import InventoryAdapter

    app.setup_extension("sphinx.ext.intersphinx")

    # Inventory contains documented name
    InventoryAdapter(app.env).main_inventory["py:class"] = {
        docname: _InventoryItem(
            project_name="TestProj",
            project_version="1",
            uri="https://x.com",
            display_name=docname.split(".")[-1],
        ),
    }
    # Node contains name from code
    node = pending_xref(refdomain="py", reftarget=qualname, reftype="class")

    resolved = _last_resolve(app, app.env, node, TextElement())
    assert isinstance(resolved, reference)
    assert resolved["refuri"] == "https://x.com"
    assert resolved["reftitle"] == "(in TestProj v1)"


@pytest.mark.parametrize("qualname", ["testmod.Class", "nonexistent.Class"])
def test_resolve_failure(app: Sphinx, qualname: str) -> None:
    from docutils.nodes import TextElement
    from sphinx.addnodes import pending_xref

    app.setup_extension("sphinx.ext.intersphinx")
    node = pending_xref(refdomain="py", reftarget=qualname, reftype="class")

    resolved = _last_resolve(app, app.env, node, TextElement())
    assert resolved is None
    type_ex, target_ex = qualname_overrides.get(
        ("py:class", qualname), (None, qualname)
    )
    if type_ex is not None:
        assert node["refdomain"], node["reftype"] == type_ex.split(":", 1)
    assert node["reftarget"] == target_ex


# These guys aren’t listed as classes in Python’s intersphinx index:
@pytest.mark.parametrize(
    "annotation",
    [
        Any,
        AnyStr,
        NoReturn,
        Callable[[int], None],
        int | str,
        int | str | None,
    ],
    ids=lambda p: str(p).replace("typing.", ""),
)
def test_typing_classes(app: Sphinx, annotation: type) -> None:
    app.config.typehints_fully_qualified = True
    name = (
        getattr(annotation, "_name", None)
        or getattr(annotation, "__name__", None)
        or getattr(get_origin(annotation), "_name", None)
    )
    output = typehints_formatter(annotation, app.config)
    assert output is None or output.startswith(f":py:data:`typing.{name}")


@pytest.mark.parametrize(
    "legacy_autodoc",
    [
        pytest.param(
            True,
            id="legacy",
            marks=pytest.mark.sphinx(
                confoverrides=dict(autodoc_use_legacy_class_based=True)
            ),
        ),
        pytest.param(
            False,
            id="latest",
            marks=pytest.mark.xfail(
                Version(version("sphinx")) >= Version("9"),
                reason="Sphinx 9+ uses different autodoc implementation.",
            ),
        ),
    ],
)
@pytest.mark.parametrize(
    ("direc", "base", "sub"),
    [
        pytest.param("autoclass", "Class", "SubCl", id="class"),
        pytest.param("autoexception", "Excep", "Excep2", id="exception"),
    ],
)
def test_autodoc(
    *,
    subtests: pytest.Subtests,
    app: Sphinx,
    testmod: ModuleType,  # noqa: ARG001
    legacy_autodoc: bool,
    direc: str,
    base: str,
    sub: str,
) -> None:
    """Test that autodoc respects qualname_overrides after patching it."""
    Path(app.srcdir, "index.rst").write_text(
        f"""\
.. {direc}:: testmod.{sub}
   :show-inheritance:
""",
    )
    assert app.config.autodoc_use_legacy_class_based is legacy_autodoc
    app.build()
    out = Path(app.outdir, "index.html").read_text()
    with subtests.test("no warnings"):
        assert not (ws := cast("StringIO", app._warning).getvalue()), ws  # noqa: SLF001
    with subtests.test("text-override"):
        assert re.search(
            r'<(code|span)?[^>]*><span class="pre">test\.</span></(code|span)>'
            f'<(code|span)?[^>]*><span class="pre">{sub}</span></(code|span)>',
            out,
        ), out
    with subtests.test("link-override"):
        assert f'<a class="headerlink" href="#test.{sub}"' in out, out
    with subtests.test("bases"):
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
    buf = cast("StringIO", app._warning)  # noqa: SLF001
    warnings_ = [
        w
        for w in buf.getvalue().splitlines()
        if "Cannot treat a function defined as a local function" not in w
    ]
    assert not warnings_, warnings_
    # TODO(flying-sheep): actually reproduce
    # https://github.com/theislab/scanpydoc/issues/14
    assert "fwd_mod.A" in out, out


@pytest.mark.parametrize(
    "docstring",
    [
        """
        :param x: An x
        :returns: foo
                      A foo!
                  bar
                      A bar!
        """,
        """
        :returns: foo
                      A foo!
                  bar
                      A bar!
        :param x: An x
        """,
        """
        Parameters
        ----------
        x
            An x

        Returns
        -------
        foo
            A foo!
        bar
            A bar!
        """,
    ],
    ids=["last", "first", "numpydoc"],
)
@pytest.mark.parametrize(
    ("return_ann", "foo_rendered"),
    [
        pytest.param(tuple[str, int], ":py:class:`str`", id="tuple"),
        pytest.param(tuple[str, int] | None, ":py:class:`str`", id="tuple | None"),
        pytest.param(
            tuple[Mapping[str, float], int],
            r":py:class:`~collections.abc.Mapping`\ \["
            ":py:class:`str`, :py:class:`float`"
            "]",
            id="complex",
        ),
        pytest.param(int | None, None, id="int | None"),
    ],
)
def test_return_tuple(
    process_doc: ProcessDoc,
    docstring: str,
    return_ann: type,
    foo_rendered: str | None,
) -> None:
    is_numpydoc = "-----" in docstring

    def fn_test() -> None:  # pragma: no cover
        pass

    fn_test.__doc__ = docstring
    fn_test.__annotations__["return"] = return_ann
    lines = [
        l
        for l in process_doc(fn_test, run_napoleon=is_numpydoc)
        if l
        if not re.match(r"^:(rtype|param)( \w+)?:", l)
    ]
    if foo_rendered is None:
        assert lines == [
            ":returns: foo",
            "              A foo!",
            "          bar",
            "              A bar!",
        ]
    else:
        assert lines == [
            f":returns: foo : {foo_rendered}",
            "              A foo!",
            "          bar : :py:class:`int`",
            "              A bar!",
        ]


def test_return_tuple_anonymous(process_doc: ProcessDoc) -> None:
    def fn_test() -> tuple[int, str]:  # pragma: no cover
        """
        Returns
        -------
        :
            An int!
        :
            A str!
        """  # noqa: D401, D205
        return (1, "foo")

    lines = [
        l
        for l in process_doc(fn_test, run_napoleon=True)
        if l
        if not re.match(r"^:(rtype|param)( \w+)?:", l)
    ]
    assert lines == [
        ":returns: :py:class:`int`",
        "              An int!",
        "          :py:class:`str`",
        "              A str!",
    ]


def test_return_nodoc(process_doc: ProcessDoc) -> None:
    def fn() -> tuple[int, str]:  # pragma: no cover
        """No return section."""
        return 1, ""

    res = process_doc(fn)
    assert len(res) == 3  # noqa: PLR2004
    assert res[0:2] == [inspect.getdoc(fn), ""]
    assert res[2].startswith(":rtype: :sphinx_autodoc_typehints_type:")


def test_load_without_sat(make_app_setup: MakeApp) -> None:
    make_app_setup(
        master_doc="index",
        extensions=["sphinx.ext.autodoc", "scanpydoc.elegant_typehints"],
    )


def test_load_error(make_app_setup: MakeApp) -> None:
    with pytest.raises(
        RuntimeError,
        match=r"`scanpydoc.elegant_typehints` requires `sphinx.ext.autodoc`",
    ):
        make_app_setup(
            master_doc="index",
            extensions=["scanpydoc.elegant_typehints"],
        )

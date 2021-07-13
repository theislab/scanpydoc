import inspect
import re
import sys
import typing as t
from pathlib import Path

try:  # 3.8 additions
    from typing import Literal, get_args, get_origin
except ImportError:
    from typing_extensions import Literal, get_args, get_origin

import pytest
import sphinx_autodoc_typehints as sat
from sphinx.application import Sphinx

from scanpydoc.elegant_typehints.formatting import (
    format_annotation,
    _format_terse,
    _format_full,
)
from scanpydoc.elegant_typehints.return_tuple import process_docstring


@pytest.fixture
def _testmod(make_module):
    return make_module(
        "_testmod",
        """\
        class Class: pass
        class SubCl(Class): pass
        class Excep(RuntimeError): pass
        class Excep2(Excep): pass
        """,
    )


@pytest.fixture
def app(make_app_setup) -> Sphinx:
    return make_app_setup(
        master_doc="index",
        extensions=[
            "sphinx.ext.autodoc",
            "sphinx.ext.napoleon",
            "sphinx_autodoc_typehints",
            "scanpydoc.elegant_typehints",
        ],
        qualname_overrides={
            "_testmod.Class": "test.Class",
            "_testmod.SubCl": "test.SubCl",
            "_testmod.Excep": "test.Excep",
            "_testmod.Excep2": "test.Excep2",
        },
    )


@pytest.fixture
def process_doc(app):
    app.config.typehints_fully_qualified = True

    def process(fn: t.Callable) -> t.List[str]:
        lines = inspect.getdoc(fn).split("\n")
        sat.process_docstring(app, "function", fn.__name__, fn, None, lines)
        process_docstring(app, "function", fn.__name__, fn, None, lines)
        return lines

    return process


def test_app(app):
    assert "qualname_overrides" in app.config.values
    assert "_testmod.Class" in app.config.qualname_overrides


def test_default(app):
    assert format_annotation(str) == ":py:class:`str`"


def test_alternatives(process_doc):
    def fn_test(s: str):
        """
        :param s: Test
        """

    assert process_doc(fn_test) == [
        ":type s: "
        r":annotation-terse:`:py:class:\`str\``\ "
        r":annotation-full:`:py:class:\`str\``",
        ":param s: Test",
    ]


def test_defaults_simple(process_doc):
    def fn_test(s: str = "foo", n: None = None, i_: int = 1):
        r"""
        :param s: Test S
        :param n: Test N
        :param i\_: Test I
        """

    assert process_doc(fn_test) == [
        ":type s: "
        r":annotation-terse:`:py:class:\`str\``\ "
        r":annotation-full:`:py:class:\`str\`` "
        "(default: ``'foo'``)",
        ":param s: Test S",
        ":type n: "
        r":annotation-terse:`:py:obj:\`None\``\ "
        r":annotation-full:`:py:obj:\`None\`` "
        "(default: ``None``)",
        ":param n: Test N",
        r":type i\_: "
        r":annotation-terse:`:py:class:\`int\``\ "
        r":annotation-full:`:py:class:\`int\`` "
        "(default: ``1``)",
        r":param i\_: Test I",
    ]


def test_defaults_complex(process_doc):
    def fn_test(m: t.Mapping[str, int] = {}):
        """
        :param m: Test M
        """

    assert process_doc(fn_test) == [
        ":type m: "
        r":annotation-terse:`:py:class:\`typing.Mapping\``\ "
        r":annotation-full:`"
        r":py:class:\`typing.Mapping\`\[:py:class:\`str\`, :py:class:\`int\`]"
        "` (default: ``{}``)",
        ":param m: Test M",
    ]


def test_mapping(app):
    assert _format_terse(t.Mapping[str, t.Any]) == ":py:class:`~typing.Mapping`"
    assert _format_full(t.Mapping[str, t.Any]) == (
        r":py:class:`~typing.Mapping`\["
        r":py:class:`str`, "
        r":py:data:`~typing.Any`"
        r"]"
    )


def test_dict(app):
    assert _format_terse(t.Dict[str, t.Any]) == (
        "{:py:class:`str`: :py:data:`~typing.Any`}"
    )


@pytest.mark.parametrize(
    "annotation,expected",
    [
        (t.Callable[..., t.Any], "(…) → :py:data:`~typing.Any`"),
        (
            t.Callable[[str, int], None],
            "(:py:class:`str`, :py:class:`int`) → :py:obj:`None`",
        ),
    ],
)
def test_callable_terse(app, annotation, expected):
    assert _format_terse(annotation) == expected


def test_literal(app):
    assert _format_terse(Literal["str", 1, None]) == "{'str', 1, None}"
    assert _format_full(Literal["str", 1, None]) == (
        r":py:data:`~typing.Literal`\['str', 1, None]"
    )


def test_qualname_overrides_class(app, _testmod):
    assert _testmod.Class.__module__ == "_testmod"
    assert _format_terse(_testmod.Class) == ":py:class:`~test.Class`"


def test_qualname_overrides_exception(app, _testmod):
    assert _testmod.Excep.__module__ == "_testmod"
    assert _format_terse(_testmod.Excep) == ":py:exc:`~test.Excep`"


def test_qualname_overrides_recursive(app, _testmod):
    assert _format_terse(t.Union[_testmod.Class, str]) == (
        r":py:class:`~test.Class` | :py:class:`str`"
    )
    assert _format_full(t.Union[_testmod.Class, str]) == (
        r":py:data:`~typing.Union`\["
        r":py:class:`~test.Class`, "
        r":py:class:`str`"
        r"]"
    )


def test_fully_qualified(app, _testmod):
    assert _format_terse(t.Union[_testmod.Class, str], True) == (
        r":py:class:`test.Class` | :py:class:`str`"
    )
    assert _format_full(t.Union[_testmod.Class, str], True) == (
        r":py:data:`typing.Union`\[" r":py:class:`test.Class`, " r":py:class:`str`" r"]"
    )


def test_classes_get_added(app, parse):
    doc = parse(app, r":annotation-full:`:py:class:\`str\``")
    assert doc[0].tagname == "paragraph"
    assert doc[0][0].tagname == "inline"
    assert doc[0][0]["classes"] == ["annotation", "full"]
    # print(doc.asdom().toprettyxml())


@pytest.mark.parametrize("formatter", [_format_terse, _format_full], ids="tf")
# These guys aren’t listed as classes in Python’s intersphinx index:
@pytest.mark.parametrize(
    "annotation",
    [
        t.Any,
        t.AnyStr,
        # t.NoReturn,
        t.Callable[[int], None],
        # t.ClassVar[t.Any],
        t.Optional[int],
        t.Tuple[int, str],
        t.Tuple[float, ...],
        t.Union[int, str],
        t.Union[int, str, None],
    ],
    ids=lambda p: str(p).replace("typing.", ""),
)
def test_typing_classes(app, annotation, formatter):
    name = (
        getattr(annotation, "_name", None)
        or getattr(annotation, "__name__", None)
        or getattr(get_origin(annotation), "_name", None)
        # 3.6 _Any and _Union
        or annotation.__class__.__name__[1:]
    )
    if formatter is _format_terse and name in {"Union", "Callable"}:
        pytest.skip("Tested elsewhere")
    args = get_args(annotation)
    if name == "Union" and len(args) == 2 and type(None) in args:
        name = "Optional"
    assert formatter(annotation, True).startswith(f":py:data:`typing.{name}")


def test_typing_class_nested(app):
    assert _format_full(t.Optional[t.Tuple[int, str]]) == (
        ":py:data:`~typing.Optional`\\["
        ":py:data:`~typing.Tuple`\\[:py:class:`int`, :py:class:`str`]"
        "]"
    )


@pytest.mark.parametrize(
    "direc,base,sub",
    [
        ("autoclass", "Class", "SubCl"),
        ("autoexception", "Excep", "Excep2"),
    ],
)
def test_autodoc(app, _testmod, direc, base, sub):
    Path(app.srcdir, "index.rst").write_text(
        f"""\
.. {direc}:: _testmod.{sub}
   :show-inheritance:
"""
    )
    app.build()
    out = Path(app.outdir, "index.html").read_text()
    assert not app._warning.getvalue(), app._warning.getvalue()
    assert re.search(
        r'<(code|span)?[^>]*><span class="pre">test\.</span></(code|span)>'
        f'<(code|span)?[^>]*><span class="pre">{sub}</span></(code|span)>',
        out,
    ), out
    assert f'<a class="headerlink" href="#test.{sub}"' in out, out
    assert re.search(rf"Bases: <code[^>]*><span[^>]*>test\.{base}", out), out


@pytest.mark.skipif(sys.version_info < (3, 7), reason="bpo-34776 only fixed on 3.7+")
def test_fwd_ref(app, make_module):
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
        f"""\
.. autosummary::

   fwd_mod.A
   fwd_mod.B
"""
    )
    app.setup_extension("sphinx.ext.autosummary")

    app.build()

    out = Path(app.outdir, "index.html").read_text()
    warnings = [
        w
        for w in app._warning.getvalue().splitlines()
        if "Cannot treat a function defined as a local function" not in w
    ]
    assert not warnings, warnings
    # TODO: actually reproduce #14
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
    "return_ann",
    [t.Tuple[str, int], t.Optional[t.Tuple[str, int]]],
    ids=["Tuple", "Optional[Tuple]"],
)
def test_return(process_doc, docstring, return_ann):
    def fn_test():
        pass

    fn_test.__doc__ = docstring
    fn_test.__annotations__["return"] = return_ann
    lines = [
        l
        for l in process_doc(fn_test)
        if not re.match("^:(rtype|param|annotation-(full|terse)):", l)
    ]
    assert lines == [
        r":return: foo : "
        r":annotation-terse:`:py:class:\`str\``\ "
        r":annotation-full:`:py:class:\`str\``",
        "             A foo!",
        r"         bar : "
        r":annotation-terse:`:py:class:\`int\``\ "
        r":annotation-full:`:py:class:\`int\``",
        "             A bar!",
    ]


def test_return_too_many(process_doc):
    def fn_test() -> t.Tuple[int, str]:
        """
        :return: foo
                     A foo!
                 bar
                     A bar!
                 baz
                     A baz!
        """

    assert not any(
        "annotation-terse" in l
        for l in process_doc(fn_test)
        if not l.startswith(":rtype:")
    )
